# archive/

Old hardware artifacts kept for reference only. **Nothing here is used by the
live Pi system** (`app.py` / `main.py` / `hardware/`).

## phECarduino.ino

The original **standalone pH/EC calibration station**: an Arduino that was the
I2C master to the Atlas Scientific EZO pH (`0x63`) and EC (`0x64`) circuits,
with a 16x2 LCD and a rotary encoder for a manual "Calibrate? / pH Cal / EC Cal"
menu.

This was superseded when the EZO circuits were moved onto the Raspberry Pi via
an I2C shield. The Pi is now the **sole I2C master** for those circuits
(`hardware/rpi_ezo_sensors.py`), and calibration is done from the Pi:

- `POST /api/sensors/ph/calibrate`
- `POST /api/sensors/ec/calibrate`
- `GET  /api/sensors/calibration/status`

> ⚠️ **Do not re-attach this Arduino to the EZO I2C bus while the Pi is running.**
> I2C allows only one master per bus; two masters on the same `0x63`/`0x64`
> circuits will corrupt readings.
