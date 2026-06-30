# Soil sensor ESP32 firmware

Reference Arduino sketch for the wireless soil sensors. One sketch flashed to
every board; only `SENSOR_ID` (and the shared WiFi/broker creds) changes.

## Build
- Arduino IDE with the ESP32 core, OR PlatformIO.
- Library: `PubSubClient` (Nick O'Leary).

## Per-board steps
1. `cp config.sample.h config.h`
2. Set `SENSOR_ID` to a unique value that matches a key in `config.SOIL_SENSORS`
   on the Pi.
3. Fill in `WIFI_SSID`, `WIFI_PASSWORD`, `MQTT_HOST`, `MQTT_USERNAME`,
   `MQTT_PASSWORD`.
4. Flash. Open the serial monitor at 115200 baud to see connect status.

## Wiring (default pin assignments)
- Capacitive soil probe analog out → GPIO34 (`MOISTURE_PIN`).
- Optional battery via 2:1 divider → GPIO35 (`BATTERY_PIN`).
- USB power for the recommended wired install — no battery wiring needed.

## Topics
- `grow/soil/{SENSOR_ID}` — reading JSON (QoS 1, not retained).
- `grow/soil/{SENSOR_ID}/status` — `online` on connect, `offline` via Last Will
  on drop (QoS 1, retained).

## Calibration
With the probe in air, note the raw ADC value printed in the serial log and
set `MOISTURE_RAW_DRY`. Submerge in water, set `MOISTURE_RAW_WET`. The percent
mapping is linear between those two points.
