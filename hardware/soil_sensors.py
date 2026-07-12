#!/usr/bin/env python3
"""
Soil Sensor Manager - MQTT subscriber for wireless ESP32 soil probes.

Each ESP32 publishes a JSON reading (moisture, temp, optional EC, batt, rssi)
to ``grow/soil/{sensor_id}`` and a retained status (``online`` / ``offline``
via MQTT Last Will) to ``grow/soil/{sensor_id}/status``. This module runs a
single paho MQTT client in a background thread and caches the latest reading
per sensor behind a lock, mirroring the ``TankMonitorManager`` lifecycle so
the rest of the system (``main.py`` / ``hardware_comms.py`` / ``app.py``)
treats it the same way.
"""

import json
import logging
import random
import threading
from datetime import datetime
from typing import Dict, Optional

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False

from config import MOCK_SETTINGS

logger = logging.getLogger(__name__)


class SoilSensor:
    """A single registered soil sensor — registry entry + cached latest reading."""

    def __init__(self, sensor_id: int, name: str, room: str, expected_interval_s: int):
        self.sensor_id = sensor_id
        self.name = name
        self.room = room
        self.expected_interval_s = expected_interval_s

        # Latest reading (None until first message arrives)
        self.moisture: Optional[float] = None
        self.temp: Optional[float] = None
        self.ec: Optional[float] = None
        self.batt: Optional[float] = None
        self.rssi: Optional[int] = None
        self.last_update: Optional[datetime] = None

        # True once the broker reports the device online (retained "online"
        # or any fresh reading); flipped False by the LWT "offline" message.
        self.online_flag: bool = False

    def to_dict(self) -> Dict:
        """Snapshot of the current state. Status is computed by the manager."""
        return {
            'sensor_id': self.sensor_id,
            'name': self.name,
            'room': self.room,
            'moisture': self.moisture,
            'temp': self.temp,
            'ec': self.ec,
            'batt': self.batt,
            'rssi': self.rssi,
            'last_update': self.last_update.isoformat() if self.last_update else None,
        }


class MockSoilSensor(SoilSensor):
    """A SoilSensor that fabricates plausible drifting readings (no broker)."""

    def __init__(self, sensor_id: int, name: str, room: str, expected_interval_s: int):
        super().__init__(sensor_id, name, room, expected_interval_s)
        # Seed plausible values so the dashboard has data immediately.
        self.moisture = round(35 + random.random() * 20, 1)  # 35-55 %
        self.temp = round(20.5 + random.random() * 1.5, 1)
        self.ec = round(1.4 + random.random() * 0.6, 2)
        self.batt = round(3.85 + random.random() * 0.15, 2)
        self.rssi = -55 - int(random.random() * 25)
        self.last_update = datetime.now()
        self.online_flag = True

    def refresh(self):
        """Drift the mock reading slightly and bump last_update."""
        self.moisture = max(20.0, min(70.0, self.moisture + (random.random() - 0.5) * 1.5))
        self.moisture = round(self.moisture, 1)
        self.temp = round(self.temp + (random.random() - 0.5) * 0.2, 1)
        self.ec = round(max(0.5, self.ec + (random.random() - 0.5) * 0.05), 2)
        self.batt = round(max(3.3, self.batt - random.random() * 0.001), 2)
        self.rssi = -55 - int(random.random() * 25)
        self.last_update = datetime.now()
        self.online_flag = True


class SoilSensorManager:
    """
    Owns a single paho MQTT client running in a background thread and caches
    the latest reading per sensor. Mirror of ``TankMonitorManager``.
    """

    TOPIC_READING_WILDCARD = "grow/soil/+"
    TOPIC_STATUS_WILDCARD = "grow/soil/+/status"

    def __init__(self,
                 broker_host: str = "localhost",
                 broker_port: int = 1883,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 use_mock: bool = False):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.use_mock = use_mock or MOCK_SETTINGS.get('soil_sensors', False)

        self.sensors: Dict[int, SoilSensor] = {}
        self._lock = threading.Lock()

        self._client = None
        self._started = False

    # ---------------------------------------------------------------- registry

    def register(self, sensor_id: int, name: str, room: str, expected_interval_s: int):
        """Pre-seed a sensor in the registry. Safe to call before start_all()."""
        with self._lock:
            if sensor_id in self.sensors:
                logger.warning(f"Soil sensor {sensor_id}: already registered")
                return
            cls = MockSoilSensor if self.use_mock else SoilSensor
            self.sensors[sensor_id] = cls(sensor_id, name, room, expected_interval_s)
            logger.info(
                f"Soil sensor {sensor_id} registered "
                f"(name='{name}', room='{room}', interval={expected_interval_s}s, mock={self.use_mock})"
            )

    # -------------------------------------------------------------- lifecycle

    def start_all(self):
        """Connect to MQTT and start the network loop (or no-op for mock)."""
        if self._started:
            return

        if self.use_mock:
            logger.info("SoilSensorManager: mock mode — no broker connection")
            self._started = True
            return

        if not HAS_MQTT:
            logger.error(
                "SoilSensorManager: paho-mqtt not installed — "
                "soil sensor cache will stay empty. `pip install paho-mqtt`."
            )
            return

        try:
            # CallbackAPIVersion only exists on paho >= 2; fall back gracefully.
            try:
                self._client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION2,
                    client_id="batch-dashboard-soil",
                )
            except AttributeError:
                self._client = mqtt.Client(client_id="batch-dashboard-soil")

            if self.username:
                self._client.username_pw_set(self.username, self.password)

            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect

            # Auto-reconnect with backoff; broker may be down at boot.
            self._client.reconnect_delay_set(min_delay=1, max_delay=30)

            self._client.connect_async(self.broker_host, self.broker_port, keepalive=60)
            self._client.loop_start()
            self._started = True
            logger.info(
                f"SoilSensorManager: MQTT loop started "
                f"(broker={self.broker_host}:{self.broker_port})"
            )
        except Exception as e:
            logger.error(f"SoilSensorManager: failed to start MQTT client: {e}")
            self._client = None

    def stop_all(self):
        """Stop the MQTT loop and disconnect."""
        if not self._started:
            return
        self._started = False

        if self._client is None:
            return

        try:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("SoilSensorManager: MQTT loop stopped")
        except Exception as e:
            logger.warning(f"SoilSensorManager: error during stop: {e}")
        finally:
            self._client = None

    # ---------------------------------------------------------------- read API

    def get_readings(self, sensor_id: Optional[int] = None) -> Dict:
        """
        Return the latest reading(s) with derived ``status`` field.

        - status = 'offline' if the broker reported offline via LWT
        - status = 'stale' if the last reading is older than 2*interval
        - status = 'online' otherwise (only if we actually have a reading)
        """
        with self._lock:
            if sensor_id is not None:
                sensor = self.sensors.get(sensor_id)
                if sensor is None:
                    return {'error': f'No sensor {sensor_id}'}
                if self.use_mock and isinstance(sensor, MockSoilSensor):
                    sensor.refresh()
                return self._snapshot(sensor)

            result = {}
            for sid, sensor in self.sensors.items():
                if self.use_mock and isinstance(sensor, MockSoilSensor):
                    sensor.refresh()
                result[sid] = self._snapshot(sensor)
            return result

    def get_sensor_count(self) -> int:
        return len(self.sensors)

    def get_online_count(self) -> int:
        with self._lock:
            return sum(
                1 for s in self.sensors.values()
                if self._derive_status(s) == 'online'
            )

    # ---------------------------------------------------------------- helpers

    def _snapshot(self, sensor: SoilSensor) -> Dict:
        d = sensor.to_dict()
        d['status'] = self._derive_status(sensor)
        return d

    def _derive_status(self, sensor: SoilSensor) -> str:
        if not sensor.online_flag:
            return 'offline'
        if sensor.last_update is None:
            return 'offline'
        age_s = (datetime.now() - sensor.last_update).total_seconds()
        if age_s > 2 * sensor.expected_interval_s:
            return 'stale'
        return 'online'

    # ----------------------------------------------------------- mqtt callbacks

    # NOTE: paho calls these on its network thread. Keep them short and never
    # let a malformed payload kill the loop.

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        # paho v2 hands us reason_code; v1 hands us an int rc. Both stringify fine.
        logger.info(f"SoilSensorManager: connected to MQTT broker (rc={reason_code})")
        try:
            client.subscribe([(self.TOPIC_READING_WILDCARD, 1),
                              (self.TOPIC_STATUS_WILDCARD, 1)])
        except Exception as e:
            logger.error(f"SoilSensorManager: subscribe failed: {e}")

    def _on_disconnect(self, client, userdata, *args, **kwargs):
        # paho will auto-reconnect via reconnect_delay_set; just log.
        logger.warning("SoilSensorManager: MQTT disconnected (auto-reconnect armed)")

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            parts = topic.split('/')
            # grow/soil/{id}  OR  grow/soil/{id}/status
            if len(parts) < 3 or parts[0] != 'grow' or parts[1] != 'soil':
                return
            try:
                sensor_id = int(parts[2])
            except ValueError:
                logger.debug(f"Soil MQTT: non-int sensor id in topic {topic!r}")
                return

            is_status = len(parts) == 4 and parts[3] == 'status'

            with self._lock:
                sensor = self.sensors.get(sensor_id)
                if sensor is None:
                    # Heard from an unregistered device — log once at debug, ignore.
                    logger.debug(f"Soil MQTT: ignoring unregistered sensor {sensor_id}")
                    return

                if is_status:
                    payload = msg.payload.decode('utf-8', errors='ignore').strip().lower()
                    if payload == 'online':
                        sensor.online_flag = True
                    elif payload == 'offline':
                        sensor.online_flag = False
                    else:
                        logger.debug(f"Soil MQTT: unknown status payload {payload!r} for {sensor_id}")
                    return

                # Reading
                try:
                    data = json.loads(msg.payload.decode('utf-8', errors='ignore'))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"Soil MQTT: bad JSON from sensor {sensor_id}: {e}")
                    return

                sensor.moisture = _coerce_float(data.get('moisture'))
                sensor.temp = _coerce_float(data.get('temp'))
                sensor.ec = _coerce_float(data.get('ec'))  # may be None
                sensor.batt = _coerce_float(data.get('batt'))
                rssi = data.get('rssi')
                sensor.rssi = int(rssi) if rssi is not None else None
                sensor.last_update = datetime.now()
                sensor.online_flag = True

        except Exception as e:
            # MUST NOT let one bad message kill the loop.
            logger.error(f"SoilSensorManager: error handling message: {e}")


def _coerce_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
