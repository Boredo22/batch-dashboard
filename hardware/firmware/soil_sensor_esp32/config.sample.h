// Copy this file to `config.h` (gitignored) and fill in real values per board.
// SENSOR_ID is the only thing that changes between boards.

#pragma once

#define SENSOR_ID 1                   // must match a key in config.SOIL_SENSORS

#define WIFI_SSID     "your-ssid"
#define WIFI_PASSWORD "your-wifi-password"

#define MQTT_HOST     "192.168.1.10"  // Raspberry Pi LAN IP
#define MQTT_PORT     1883
#define MQTT_USERNAME "grow"          // matches scripts/setup_mosquitto.sh
#define MQTT_PASSWORD "your-broker-password"

// Optional tunables — uncomment to override defaults in soil_sensor_esp32.ino:
// #define PUBLISH_INTERVAL_MS  60000
// #define MOISTURE_PIN         34
// #define BATTERY_PIN          35
// #define MOISTURE_RAW_DRY     3000
// #define MOISTURE_RAW_WET     1200
// #define BATTERY_DIVIDER_RATIO 2.0
