Trigger emergency stop - turns off all relays and stops all operations.

## Via API
```bash
curl -X POST http://localhost:5000/api/emergency/stop
```

## Via Direct Hardware (if API is unresponsive)
```bash
python3 -c "
from hardware.hardware_comms import emergency_stop
result = emergency_stop()
print('Emergency stop:', 'SUCCESS' if result else 'FAILED')
"
```

## Manual GPIO Reset (last resort)
```bash
python3 -c "
import lgpio
h = lgpio.gpiochip_open(0)
relay_pins = [22, 26, 20, 21, 16, 19, 12, 13, 10, 9, 0, 5]
for pin in relay_pins:
    try:
        lgpio.gpio_claim_output(h, pin, 0)  # Set LOW (relay off)
        print(f'GPIO {pin} set LOW')
    except: pass
lgpio.gpiochip_close(h)
print('All relay GPIOs set to LOW')
"
```