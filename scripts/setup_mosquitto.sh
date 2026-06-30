#!/usr/bin/env bash
# Install + configure the Mosquitto MQTT broker for the wireless soil sensors.
#
# Security model: the broker is bound to the LAN only, requires a username +
# password, and MUST NOT be port-forwarded to the public internet. If remote
# access is ever needed, route it through a VPN or push the data upward via a
# (future) Supabase historian — never expose 1883.
#
# Usage:
#   sudo bash scripts/setup_mosquitto.sh
#   # then export the same creds in your environment / systemd unit:
#   #   SOIL_MQTT_USERNAME=grow
#   #   SOIL_MQTT_PASSWORD=<the password you just set>

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Re-run with sudo." >&2
  exit 1
fi

MQTT_USER="${MQTT_USER:-grow}"
CONF_DIR="/etc/mosquitto/conf.d"
PASSWD_FILE="/etc/mosquitto/passwd"
CONF_FILE="$CONF_DIR/grow.conf"

echo ">>> Installing mosquitto + clients..."
apt-get update
apt-get install -y mosquitto mosquitto-clients

echo ">>> Creating broker user '$MQTT_USER' (you'll be prompted for a password)..."
# -c truncates; only create if it doesn't already have the user. To rotate a
# password later, run: sudo mosquitto_passwd /etc/mosquitto/passwd $MQTT_USER
if [[ ! -f "$PASSWD_FILE" ]]; then
  mosquitto_passwd -c "$PASSWD_FILE" "$MQTT_USER"
else
  echo "    $PASSWD_FILE exists; updating '$MQTT_USER'"
  mosquitto_passwd "$PASSWD_FILE" "$MQTT_USER"
fi
chown mosquitto:mosquitto "$PASSWD_FILE"
chmod 640 "$PASSWD_FILE"

echo ">>> Writing $CONF_FILE..."
mkdir -p "$CONF_DIR"
cat > "$CONF_FILE" <<'EOF'
# Soil-sensor MQTT listener — LAN only, auth required.
# Listening on 0.0.0.0:1883 lets ESP32s on the LAN reach the broker without
# exposing it externally — keep firewall rules / router config matching this.
listener 1883 0.0.0.0
allow_anonymous false
password_file /etc/mosquitto/passwd

# Keep messages small and forget old retained ones cheaply.
persistence true
persistence_location /var/lib/mosquitto/

log_dest syslog
EOF

echo ">>> Enabling and starting mosquitto..."
systemctl enable --now mosquitto
systemctl restart mosquitto
sleep 1
systemctl --no-pager status mosquitto | head -n 10 || true

cat <<EOM

Done.

Smoke test (from the Pi or another LAN host):
  mosquitto_sub -h localhost -u $MQTT_USER -P '<password>' -t 'grow/soil/#' -v
  mosquitto_pub -h localhost -u $MQTT_USER -P '<password>' \\
      -t 'grow/soil/1' -m '{"moisture":42.1,"temp":21.3,"batt":3.92,"rssi":-67}'

Next, set the same creds in the Pi's env (e.g. in systemd's EnvironmentFile):
  SOIL_MQTT_HOST=localhost
  SOIL_MQTT_PORT=1883
  SOIL_MQTT_USERNAME=$MQTT_USER
  SOIL_MQTT_PASSWORD=<password>

DO NOT port-forward TCP/1883 to the internet.
EOM
