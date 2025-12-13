Check hardware connectivity and status. Run this on the Raspberry Pi to diagnose hardware issues.

## I2C Devices (Pumps at 0x0B-0x12, pH at 0x63, EC at 0x64)
```bash
i2cdetect -y 1
```

## GPIO Pin Status
```bash
python3 -c "
import lgpio
h = lgpio.gpiochip_open(0)
pins = [22, 26, 20, 21, 16, 19, 12, 13, 10, 9, 0, 5, 23, 24]
print('GPIO Pin States:')
for pin in pins:
    try:
        lgpio.gpio_claim_input(h, pin)
        val = lgpio.gpio_read(h, pin)
        print(f'  GPIO {pin:2d}: {\"HIGH\" if val else \"LOW\"}')
        lgpio.gpio_free(h, pin)
    except Exception as e:
        print(f'  GPIO {pin:2d}: Error - {e}')
lgpio.gpiochip_close(h)
"
```

## Serial Ports (Arduino)
```bash
ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || echo "No serial devices found"
```

## System Status via API
```bash
curl -s http://localhost:5000/api/status | python3 -m json.tool
```