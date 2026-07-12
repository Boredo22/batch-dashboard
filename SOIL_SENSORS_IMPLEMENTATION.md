# Soil Sensor Integration — Implementation Spec

**Audience:** Claude Code, implementing inside this repo (`batch-dashboard/`).
**Goal:** Add wireless ESP32 soil sensors (moisture + temp + EC, battery/signal telemetry) to the existing Nutrient Mixing System. Scale target: **10–20 sensors**, grouped by grow room.

This document is a build plan, not finished code. Follow the existing codebase conventions — the soil sensor subsystem must mirror the **TankMonitor** pattern (`hardware/tank_monitor.py`) as closely as possible.

---

## 0. Architectural decision (already made — do not change)

Sensor data reaches the Pi over **local MQTT**, not via Supabase polling.

- Run a **Mosquitto broker on the Pi** (same box as Flask, port 1883, LAN-only).
- ESP32s **publish** readings to MQTT topics over WiFi.
- The Pi runs a background MQTT subscriber (`SoilSensorManager`) that caches the latest reading per sensor behind a lock — identical lifecycle to `TankMonitorManager`.
- The cached readings are merged into the existing `/api/system/status` payload and SSE stream, so the Svelte dashboard gets them through the connection it already has.
- **Supabase is optional and out of scope for v1.** If added later, it is a *historian* only: the Pi batches readings upward for long-term charts / off-site access. It is NOT on the live control path.

**Why MQTT over the original Supabase-polling plan:** keeps live data on the LAN (sub-second, no internet dependency for irrigation decisions), push instead of poll, and gives free device-health detection via MQTT Last Will. The grow operation must keep seeing soil data even if the WAN is down.

```
ESP32 (per zone)                 Raspberry Pi                          Browser
┌──────────────┐   WiFi/MQTT   ┌────────────────────────────────┐    ┌──────────┐
│ cap moisture │──publish────▶ │ Mosquitto broker (localhost)   │    │ Svelte   │
│ temp, EC     │ grow/soil/3   │   ▲ subscribe                  │    │ dashboard│
│ batt, rssi   │               │ SoilSensorManager (bg thread)  │    └────▲─────┘
│ (USB or      │◀─ LWT online/ │   └─ cache {id: reading+ts}    │         │ SSE
│  deep sleep) │     offline   │ build_status_data() +soil[]    ├───SSE───┘
└──────────────┘               └────────────────────────────────┘
```

---

## 1. Scope of v1

In scope:
1. Mosquitto broker on the Pi (install + config + auth).
2. `hardware/soil_sensors.py` — `SoilSensor`, `MockSoilSensor`, `SoilSensorManager` (MQTT client + cache).
3. Config registry + mock flag in `config.py`.
4. Wiring into `main.py` (`FeedControlSystem`) lifecycle.
5. Read path: helper in `hardware/hardware_comms.py`, merge into `build_status_data()` in `app.py`, expose via existing REST + SSE.
6. Frontend: extend the SSE store state, add a `SoilSensors` card component grouped by room.
7. One reference ESP32 sketch (`hardware/firmware/soil_sensor_esp32/`).

Out of scope for v1: Supabase historian, charts/sparklines, alerting/notifications, calibration UI, OTA firmware updates. Leave clean extension points but do not build these.

---

## 2. Backend — `hardware/soil_sensors.py`

Create a new module mirroring `hardware/tank_monitor.py`. Three classes.

### 2.1 `SoilSensorManager`
Owns a single `paho-mqtt` client running in a background thread. This is the analogue of `TankMonitorManager`.

Public API (mirror the Manager method names already used in `main.py`):
- `__init__(self, broker_host="localhost", broker_port=1883, username=None, password=None)`
- `register(sensor_id, name, room, expected_interval_s)` — add a sensor to the registry/cache (analogous to `add_monitor`). Pre-seeds a cache entry with `connected=False`.
- `start_all()` — connect the MQTT client, subscribe, and start the network loop thread (`client.loop_start()`).
- `stop_all()` — `client.loop_stop()` + `client.disconnect()`.
- `get_readings(self, sensor_id=None) -> dict` — thread-safe; return one sensor dict or `{id: reading}` for all. Mirror `TankMonitor.get_readings` shape (see 2.4).
- `get_sensor_count() -> int`, `get_online_count() -> int` — mirror `get_monitor_count` / `get_connected_count`.

Internals:
- A `dict` keyed by `sensor_id` holding the latest reading, guarded by a `threading.Lock`.
- `paho` callbacks:
  - `on_connect`: subscribe to `grow/soil/+` (readings) and `grow/soil/+/status` (LWT/online).
  - `on_message`: parse the sensor id from the topic, JSON-decode the payload, update the cache entry + `last_update = datetime.now()`, set `connected=True`. Wrap in try/except and log on bad payloads — never let a malformed message kill the loop.
  - `on_disconnect`: log; paho auto-reconnect should be enabled (`client.reconnect_delay_set(...)`).
- Use `client.username_pw_set(...)` when credentials are provided.
- Graceful import guard like `tank_monitor.py` does for `serial`:
  ```python
  try:
      import paho.mqtt.client as mqtt
      HAS_MQTT = True
  except ImportError:
      HAS_MQTT = False
  ```

### 2.2 Topic + payload contract
- Reading topic: `grow/soil/{sensor_id}` — retained=false, QoS 1.
  Payload JSON: `{"moisture": 42.1, "temp": 21.3, "ec": 1.8, "batt": 3.92, "rssi": -67}`
  (`ec` optional — not all probes have it; treat as nullable.)
- Status topic: `grow/soil/{sensor_id}/status` — retained=true, QoS 1.
  Payload: `"online"` (published by the device on connect) / `"offline"` (set as the MQTT **Last Will** so the broker emits it automatically when the device drops).

### 2.3 Staleness vs offline (compute on read, in the Pi)
- **offline** — broker reported `offline` via the status/LWT topic. Hard signal.
- **stale** — last reading older than `2 × expected_interval_s` (cushion for deep-sleep jitter). Computed in `get_readings()` from `last_update`.
- **online** — fresh reading within window.
Return a `status` string (`"online" | "stale" | "offline"`) in each reading dict so the frontend doesn't recompute time math.

### 2.4 `get_readings()` return shape (match TankMonitor style)
```python
{
    "sensor_id": 3,
    "name": "Flower Room A - Plant 3",
    "room": "Flower A",
    "moisture": 42.1,
    "temp": 21.3,
    "ec": 1.8,            # may be None
    "batt": 3.92,
    "rssi": -67,
    "status": "online",   # online | stale | offline
    "last_update": "2026-06-30T14:05:12.345678",  # ISO, or None
}
```

### 2.5 `MockSoilSensor` / mock mode
Mirror `MockTankMonitor`: when mock mode is on, the manager fabricates plausible readings for the registered sensors (e.g. moisture drifting 35–55%, temp ~21°C, batt ~3.9V, `status="online"`, fresh `last_update`) **without connecting to any broker**. This lets the dashboard and `npm run dev` work with no hardware. Gate it on `MOCK_SETTINGS['soil_sensors']` (see §3).

---

## 3. Config — `config.py`

Follow the existing `TANK_MONITOR_PORTS` registry style and the `MOCK_SETTINGS` dict.

1. Add MQTT broker constants near the other hardware config:
   ```python
   SOIL_MQTT_HOST = "localhost"
   SOIL_MQTT_PORT = 1883
   SOIL_MQTT_USERNAME = None   # set from env in production
   SOIL_MQTT_PASSWORD = None
   ```
   Prefer reading creds from environment / `.env` (the repo already loads a `.env`) rather than hardcoding.

2. Add the sensor registry — the single place a human edits to add sensors #1–20:
   ```python
   # sensor_id -> {name, room, expected interval seconds}
   SOIL_SENSORS = {
       1: {"name": "Flower A - Plant 1", "room": "Flower A", "interval_s": 300},
       2: {"name": "Flower A - Plant 2", "room": "Flower A", "interval_s": 300},
       # ... up to 20; grouped by room
   }
   ```

3. Add the mock flag to `MOCK_SETTINGS`:
   ```python
   MOCK_SETTINGS = {
       # ...existing keys...
       "tank_monitors": False,
       "soil_sensors": False,   # Use mock soil sensors (no broker needed)
   }
   ```

---

## 4. Wiring into `main.py` (`FeedControlSystem`)

Mirror exactly how `tank_monitor_manager` is wired (currently around lines 132–145, started ~178, cleaned up ~211).

- Import: `from hardware.soil_sensors import SoilSensorManager`
- In `__init__`, after the tank monitor block:
  ```python
  self.soil_sensor_manager = SoilSensorManager(
      broker_host=config.SOIL_MQTT_HOST,
      broker_port=config.SOIL_MQTT_PORT,
      username=config.SOIL_MQTT_USERNAME,
      password=config.SOIL_MQTT_PASSWORD,
      use_mock=MOCK_SETTINGS.get("soil_sensors", False),
  )
  for sid, meta in config.SOIL_SENSORS.items():
      self.soil_sensor_manager.register(sid, meta["name"], meta["room"], meta["interval_s"])
  if self.soil_sensor_manager.get_sensor_count() > 0:
      logger.info(f"✓ {self.soil_sensor_manager.get_sensor_count()} soil sensor(s) registered")
  ```
- In the system `start()` method, alongside `tank_monitor_manager.start_all()`:
  ```python
  if self.soil_sensor_manager.get_sensor_count() > 0:
      self.soil_sensor_manager.start_all()
  ```
- In cleanup, alongside `tank_monitor_manager.stop_all()`:
  ```python
  if self.soil_sensor_manager:
      self.soil_sensor_manager.stop_all()
  ```

---

## 5. Read path → API + SSE

The dashboard already consumes `build_status_data()` over both `/api/system/status` and the SSE stream `/api/system/status/stream`. Add soil data there once; both endpoints get it for free.

1. **`hardware/hardware_comms.py`** — add a `get_soil_sensor_readings(sensor_id=None)` accessor mirroring the existing `get_tank_monitor_readings` (method ~907 + module-level wrapper ~1156). It should read from the active `FeedControlSystem.soil_sensor_manager`.

2. **`hardware/__init__` / `app.py` import line** — `app.py` currently imports `get_tank_monitor_readings` from `hardware_comms` (line ~31). Add `get_soil_sensor_readings` to that import.

3. **`app.py` → `build_status_data()`** (returns dict ~648–663) — add one key alongside `'tank_monitors'`:
   ```python
   'soil_sensors': get_soil_sensor_readings(),   # {sensor_id: reading_dict}
   ```
   Do not touch the SSE generator — it already calls `build_status_data()`.

No new routes required for v1. (Optional convenience route `GET /api/soil` may be added later; not needed by the dashboard.)

---

## 6. Frontend (Svelte 5)

### 6.1 Store — `frontend/src/lib/stores/systemStatus.svelte.js`
Add `soil_sensors: []` (or `{}` matching the payload — it's keyed by id) to the `systemData` `$state` object so the new field is reactive. No connection changes; it rides the existing SSE stream.

### 6.2 Component — `frontend/src/lib/components/hardware/SoilSensors.svelte`
- Read `systemData.soil_sensors` from the store.
- **Group cards by `room`** — this is the layout that scales to 20 sensors. Render a section per room, with a responsive grid of compact cards inside.
- Each card shows: moisture (primary, large), temp, EC (hide if null), and a footer with battery, signal (rssi), and "last seen Xs ago".
- Status badge per card driven by `reading.status`: green = online, amber = stale, red = offline. A colored dot lets the whole facility be eyeballed at a glance.
- Use the existing UI primitives in `lib/components/ui/` and the Lucide icons already in the project (`@lucide/svelte`). Match the styling of the existing hardware cards in `lib/components/hardware/`.

### 6.3 Placement
Add the `SoilSensors` section to the grower-facing page (`HeadGrower.svelte` → `lib/components/growers/`) since soil status pairs naturally with the room-send workflow. Also acceptable to surface on `Dashboard.svelte`. Confirm placement with the existing nav before committing.

---

## 7. Broker setup (Pi) — document, scripted if possible

Add a short `scripts/setup_mosquitto.sh` (or document in this repo's deploy notes):
```bash
sudo apt-get install -y mosquitto mosquitto-clients
# create a LAN-only user; do NOT expose 1883 to the internet
sudo mosquitto_passwd -c /etc/mosquitto/passwd grow
# /etc/mosquitto/conf.d/grow.conf:
#   listener 1883 0.0.0.0
#   allow_anonymous false
#   password_file /etc/mosquitto/passwd
sudo systemctl enable --now mosquitto
```
Security: broker bound to the LAN only, auth required, no port-forwarding. If remote access is ever needed, that's the (future) Supabase historian path or a VPN — never an exposed broker.

---

## 8. ESP32 firmware — `hardware/firmware/soil_sensor_esp32/`

Provide one reference Arduino sketch (PlatformIO or .ino) as the flashing template.

Requirements:
- Libraries: `WiFi`, `PubSubClient` (MQTT).
- A single per-board `#define SENSOR_ID n` is the only thing that changes between boards. WiFi creds + broker IP in a `config.h` (gitignored).
- **Sensor:** capacitive soil moisture probe (analog) — *not* resistive (resistive corrodes in soil within weeks). Optional DS18B20 for temp. Read `WiFi.RSSI()` for signal and the ADC battery divider for `batt`.
- Connect to MQTT with a **Last Will**: topic `grow/soil/{id}/status`, payload `offline`, retained, QoS 1.
- On connect: publish `online` (retained) to the status topic.
- Publish a reading JSON to `grow/soil/{id}` (QoS 1) every `interval`.
- **Power strategy — document both, default to wired:**
  - *Wired (default, recommended):* USB/5V power, persistent MQTT connection, publish on a timer. Simplest, instant, no deep-sleep edge cases. Use this wherever a rooms outlet is reachable.
  - *Battery:* `esp_deep_sleep` between publishes (publish → confirm → sleep N minutes). Only for sensors that genuinely can't be wired. Note that retained `online` + LWT still gives correct status across sleep cycles only if you keep the session; simplest robust option for battery is short intervals + treating "stale" as the soft-offline signal (already handled in §2.3).

---

## 9. Dependencies & mock-first dev

- Add `paho-mqtt` to `requirements.txt`.
- The whole subsystem must run with **`MOCK_SETTINGS['soil_sensors'] = True`** and no broker, so the dashboard can be developed against mock readings. Verify `npm run dev` (port 5173 → proxy to Flask) shows mock soil cards before touching hardware.

---

## 10. Acceptance criteria

1. With `soil_sensors` mock ON and no broker: dashboard shows the registered sensors as cards grouped by room, each with mock moisture/temp/batt/signal and a green badge; data updates live over SSE.
2. With a real Mosquitto broker + one ESP32: publishing to `grow/soil/1` updates that card within ~2s (the SSE tick).
3. Killing the ESP32 flips its card to **offline** (via LWT) within the broker's keepalive window; letting a reading age past `2×interval` flips it to **stale**.
4. Adding a sensor is purely: add a row to `config.SOIL_SENSORS` + flash a board with that `SENSOR_ID`. No other code changes.
5. Scales cleanly to 20 sensors (room grouping holds; one shared MQTT connection; one SSE stream).
6. Existing functionality (pumps, relays, flow, EC/pH, tank monitors, fill/mix/send) is untouched and still passes.
7. No secrets committed: broker creds and WiFi creds come from env / gitignored config.

---

## 11. Explicit non-goals (leave hooks, don't build)
- Supabase historian / cloud sync.
- Historical charts / sparklines.
- Alerts/notifications on dry soil.
- Calibration UI and OTA firmware.

Keep the reading dict and component structure forward-compatible with these, but do not implement them in v1.
