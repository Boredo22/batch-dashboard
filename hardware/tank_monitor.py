#!/usr/bin/env python3
"""
Tank Monitor - Serial reader for per-tank pH/EC Arduino monitors.

Each tank can have a dedicated Arduino with Atlas Scientific EZO pH and EC
sensors, connected to the Raspberry Pi via USB serial. The Arduino sends
JSON readings: {"ph":X.XX,"ec":X.XX} every ~2 seconds.

This module manages connections to one or more tank monitor Arduinos and
provides the latest readings to the rest of the system.
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

from config import MOCK_SETTINGS

logger = logging.getLogger(__name__)


class TankMonitor:
    """
    Manages a single Arduino pH/EC monitor connected via USB serial.
    Reads JSON lines and caches the latest readings.
    """

    def __init__(self, tank_id: int, port: str = None, baudrate: int = 9600):
        self.tank_id = tank_id
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        self.reader_thread = None
        self._lock = threading.Lock()

        # Latest readings
        self._ph = 0.0
        self._ec = 0.0
        self._last_update = None
        self._connected = False

    def connect(self) -> bool:
        """Open serial connection to the Arduino."""
        if not HAS_SERIAL:
            logger.error("pyserial not installed - cannot connect to tank monitor")
            return False

        port = self.port or self._auto_detect_port()
        if not port:
            logger.warning(f"Tank {self.tank_id}: No serial port found")
            return False

        try:
            self.serial_conn = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=1.0
            )
            self._connected = True
            self.port = port
            logger.info(f"Tank {self.tank_id}: Connected to {port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            logger.error(f"Tank {self.tank_id}: Serial connection failed on {port}: {e}")
            self._connected = False
            return False

    def _auto_detect_port(self) -> Optional[str]:
        """Try to auto-detect the Arduino serial port."""
        if not HAS_SERIAL:
            return None

        # Look for common Arduino USB serial devices
        for port_info in serial.tools.list_ports.comports():
            desc = (port_info.description or '').lower()
            # Match Arduino Nano, Uno, or generic CH340/CP2102 USB-serial chips
            if any(kw in desc for kw in ['arduino', 'ch340', 'cp210', 'usb serial', 'usb-serial']):
                logger.info(f"Tank {self.tank_id}: Auto-detected port {port_info.device} ({port_info.description})")
                return port_info.device

        return None

    def start(self):
        """Start the background reader thread."""
        if self.running:
            return

        if not self._connected and not self.connect():
            logger.warning(f"Tank {self.tank_id}: Cannot start - not connected")
            return

        self.running = True
        self.reader_thread = threading.Thread(
            target=self._reader_loop,
            daemon=True,
            name=f"TankMonitor-{self.tank_id}"
        )
        self.reader_thread.start()
        logger.info(f"Tank {self.tank_id}: Monitor reader started")

    def stop(self):
        """Stop the reader thread and close serial connection."""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=3)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self._connected = False
        logger.info(f"Tank {self.tank_id}: Monitor stopped")

    def _reader_loop(self):
        """Background thread that reads JSON lines from the Arduino."""
        while self.running:
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    # Try to reconnect
                    time.sleep(5)
                    self.connect()
                    continue

                line = self.serial_conn.readline()
                if not line:
                    continue

                line = line.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                # Parse JSON: {"ph":X.XX,"ec":X.XX}
                try:
                    data = json.loads(line)
                    ph = float(data.get('ph', 0))
                    ec = float(data.get('ec', 0))

                    # Ignore invalid readings (-1 means sensor error)
                    if ph < 0 or ec < 0:
                        continue

                    with self._lock:
                        self._ph = ph
                        self._ec = ec
                        self._last_update = datetime.now()

                except (json.JSONDecodeError, ValueError, TypeError):
                    # Not a valid JSON line - could be startup text, skip
                    pass

            except serial.SerialException as e:
                logger.warning(f"Tank {self.tank_id}: Serial error: {e}")
                self._connected = False
                time.sleep(5)
            except Exception as e:
                logger.error(f"Tank {self.tank_id}: Reader error: {e}")
                time.sleep(1)

    def get_readings(self) -> Dict:
        """Get the latest pH/EC readings for this tank."""
        with self._lock:
            return {
                'tank_id': self.tank_id,
                'ph': self._ph,
                'ec': self._ec,
                'last_update': self._last_update.isoformat() if self._last_update else None,
                'connected': self._connected,
                'port': self.port
            }

    @property
    def connected(self) -> bool:
        return self._connected


class MockTankMonitor:
    """Mock tank monitor for development without hardware."""

    def __init__(self, tank_id: int, **kwargs):
        self.tank_id = tank_id
        self._connected = True
        self._last_update = datetime.now()

    def connect(self) -> bool:
        self._connected = True
        return True

    def start(self):
        logger.info(f"Tank {self.tank_id}: Mock monitor started")

    def stop(self):
        logger.info(f"Tank {self.tank_id}: Mock monitor stopped")

    def get_readings(self) -> Dict:
        self._last_update = datetime.now()
        return {
            'tank_id': self.tank_id,
            'ph': 6.12,
            'ec': 1.85,
            'last_update': self._last_update.isoformat(),
            'connected': True,
            'port': 'mock'
        }

    @property
    def connected(self) -> bool:
        return self._connected


class TankMonitorManager:
    """
    Manages all tank monitor connections.
    Provides a single interface to get readings from any/all tank monitors.
    """

    def __init__(self):
        self.monitors: Dict[int, TankMonitor] = {}
        self._lock = threading.Lock()

    def add_monitor(self, tank_id: int, port: str = None, baudrate: int = 9600,
                    use_mock: bool = False):
        """Add a tank monitor for a specific tank."""
        with self._lock:
            if tank_id in self.monitors:
                logger.warning(f"Tank {tank_id}: Monitor already registered")
                return

            if use_mock or MOCK_SETTINGS.get('tank_monitors', False):
                monitor = MockTankMonitor(tank_id)
            else:
                monitor = TankMonitor(tank_id, port=port, baudrate=baudrate)

            self.monitors[tank_id] = monitor
            logger.info(f"Tank {tank_id}: Monitor registered (port={port}, mock={use_mock})")

    def start_all(self):
        """Start all registered monitors."""
        for tank_id, monitor in self.monitors.items():
            try:
                monitor.start()
            except Exception as e:
                logger.error(f"Tank {tank_id}: Failed to start monitor: {e}")

    def stop_all(self):
        """Stop all monitors and close connections."""
        for tank_id, monitor in self.monitors.items():
            try:
                monitor.stop()
            except Exception as e:
                logger.error(f"Tank {tank_id}: Error stopping monitor: {e}")

    def get_readings(self, tank_id: int = None) -> Dict:
        """
        Get tank monitor readings.

        Args:
            tank_id: Specific tank ID, or None for all tanks.

        Returns:
            Single tank readings dict if tank_id specified,
            or dict of all tank readings keyed by tank_id.
        """
        if tank_id is not None:
            monitor = self.monitors.get(tank_id)
            if monitor:
                return monitor.get_readings()
            return {'error': f'No monitor for tank {tank_id}'}

        # Return all readings
        result = {}
        for tid, monitor in self.monitors.items():
            result[tid] = monitor.get_readings()
        return result

    def get_monitor_count(self) -> int:
        return len(self.monitors)

    def get_connected_count(self) -> int:
        return sum(1 for m in self.monitors.values() if m.connected)
