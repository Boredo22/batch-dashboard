#!/usr/bin/env python3
"""Fix: Use gpio_claim_alert for callbacks"""

import lgpio
import time
import signal
import sys

FLOW_GPIO = 23
pulse_count = 0
h = None
cb = None

def pulse_callback(chip, gpio, level, tick):
    global pulse_count
    pulse_count += 1
    print(f"🌊 PULSE #{pulse_count} (level={level})")

def cleanup(signum=None, frame=None):
    global h, cb
    print(f"\nFinal count: {pulse_count}")
    if cb is not None:
        cb.cancel()
    if h is not None:
        lgpio.gpiochip_close(h)
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)

h = lgpio.gpiochip_open(0)

# KEY CHANGE: Use gpio_claim_alert instead of gpio_claim_input
# This enables edge detection for callbacks
lgpio.gpio_claim_alert(h, FLOW_GPIO, lgpio.FALLING_EDGE, lgpio.SET_PULL_UP)

cb = lgpio.callback(h, FLOW_GPIO, lgpio.FALLING_EDGE, pulse_callback)

print(f"Monitoring GPIO {FLOW_GPIO} with gpio_claim_alert")
print("Run water. Ctrl+C to stop.\n")

while True:
    print(f"Pulses: {pulse_count}")
    time.sleep(1)