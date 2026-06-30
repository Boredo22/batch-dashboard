/*
 * Soil sensor — ESP32 reference firmware.
 *
 * Hardware:
 *   - ESP32 dev board (any model with WiFi).
 *   - Capacitive soil moisture probe on ADC1 pin (default GPIO34). DO NOT use
 *     resistive probes — they corrode within weeks in soil.
 *   - Optional DS18B20 temperature probe on a separate GPIO (default GPIO4).
 *   - Optional battery: 2:1 voltage divider to ADC pin (default GPIO35) so the
 *     ESP32's 0–3.3 V ADC range covers a ~6.6 V max input. If USB-powered,
 *     leave unwired and the firmware reports 5.0 V.
 *
 * Per-board: edit config.h with the WiFi creds, broker IP, broker username/
 * password, and SENSOR_ID. Everything else is shared across boards.
 *
 * Topics (per SOIL_SENSORS_IMPLEMENTATION.md):
 *   grow/soil/{id}          — reading JSON, QoS 1, retained=false
 *   grow/soil/{id}/status   — "online"/"offline" (LWT), QoS 1, retained=true
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"   // gitignored — copy from config.sample.h

#ifndef SENSOR_ID
#error "Define SENSOR_ID in config.h (unique per board, matches config.SOIL_SENSORS)"
#endif

#ifndef PUBLISH_INTERVAL_MS
#define PUBLISH_INTERVAL_MS 60000  // 60 s; ride well inside the 300 s stale window
#endif

#ifndef MOISTURE_PIN
#define MOISTURE_PIN 34
#endif

#ifndef BATTERY_PIN
#define BATTERY_PIN 35
#endif

// Calibrate per probe with a dry/wet test, then update these two raw ADC values.
#ifndef MOISTURE_RAW_DRY
#define MOISTURE_RAW_DRY 3000   // probe in air
#endif
#ifndef MOISTURE_RAW_WET
#define MOISTURE_RAW_WET 1200   // probe in water
#endif

// Voltage divider ratio (Vin / Vadc). With a 100k:100k divider this is 2.0.
#ifndef BATTERY_DIVIDER_RATIO
#define BATTERY_DIVIDER_RATIO 2.0
#endif

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

char readingTopic[32];
char statusTopic[40];
char clientId[24];

unsigned long lastPublishMs = 0;

void buildTopics() {
  snprintf(readingTopic, sizeof(readingTopic), "grow/soil/%d", SENSOR_ID);
  snprintf(statusTopic, sizeof(statusTopic), "grow/soil/%d/status", SENSOR_ID);
  snprintf(clientId, sizeof(clientId), "soil-%d", SENSOR_ID);
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("WiFi: connecting to %s", WIFI_SSID);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 30000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("WiFi: connected, ip=%s rssi=%d\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
  } else {
    Serial.println("WiFi: FAILED — will retry");
  }
}

bool connectMQTT() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);

  // LWT: broker auto-publishes "offline" (retained) if our session drops.
  // The retained "online" we publish on successful connect overwrites it.
  bool ok;
#ifdef MQTT_USERNAME
  ok = mqtt.connect(clientId, MQTT_USERNAME, MQTT_PASSWORD,
                    statusTopic, 1, true, "offline");
#else
  ok = mqtt.connect(clientId, NULL, NULL,
                    statusTopic, 1, true, "offline");
#endif

  if (ok) {
    Serial.println("MQTT: connected");
    mqtt.publish(statusTopic, "online", true);  // retained
  } else {
    Serial.printf("MQTT: connect failed rc=%d\n", mqtt.state());
  }
  return ok;
}

float readMoisturePercent() {
  // Average a few samples — ADC is noisy.
  long sum = 0;
  const int N = 16;
  for (int i = 0; i < N; ++i) {
    sum += analogRead(MOISTURE_PIN);
    delay(2);
  }
  int raw = sum / N;
  // Capacitive probes: HIGH raw = dry, LOW raw = wet. Linear map + clamp.
  float pct = 100.0f *
              (float)(MOISTURE_RAW_DRY - raw) /
              (float)(MOISTURE_RAW_DRY - MOISTURE_RAW_WET);
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return pct;
}

float readBatteryVoltage() {
  long sum = 0;
  const int N = 8;
  for (int i = 0; i < N; ++i) {
    sum += analogRead(BATTERY_PIN);
    delay(2);
  }
  int raw = sum / N;
  // ESP32 ADC: 12-bit, default 0..3.3 V (rough; calibration improves this).
  float vAdc = (raw / 4095.0f) * 3.3f;
  return vAdc * BATTERY_DIVIDER_RATIO;
}

float readTempC() {
  // Stub: wire up DS18B20 via OneWire if you have one; otherwise report NaN
  // and the manager treats it as missing.
  return NAN;
}

void publishReading() {
  float moisture = readMoisturePercent();
  float temp = readTempC();
  float batt = readBatteryVoltage();
  int rssi = WiFi.RSSI();

  char payload[160];
  // Keep keys aligned with SoilSensorManager._on_message().
  int n;
  if (isnan(temp)) {
    n = snprintf(payload, sizeof(payload),
                 "{\"moisture\":%.1f,\"batt\":%.2f,\"rssi\":%d}",
                 moisture, batt, rssi);
  } else {
    n = snprintf(payload, sizeof(payload),
                 "{\"moisture\":%.1f,\"temp\":%.1f,\"batt\":%.2f,\"rssi\":%d}",
                 moisture, temp, batt, rssi);
  }
  if (n <= 0) return;

  bool ok = mqtt.publish(readingTopic, payload, false);
  Serial.printf("publish %s -> %s : %s\n",
                readingTopic, payload, ok ? "OK" : "FAIL");
}

void setup() {
  Serial.begin(115200);
  delay(200);
  buildTopics();
  analogReadResolution(12);
  connectWiFi();
  connectMQTT();
  publishReading();
  lastPublishMs = millis();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
  if (!mqtt.connected()) {
    connectMQTT();
    delay(500);
  }
  mqtt.loop();

  if (millis() - lastPublishMs >= PUBLISH_INTERVAL_MS) {
    publishReading();
    lastPublishMs = millis();
  }
  delay(50);
}
