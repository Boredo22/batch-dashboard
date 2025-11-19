# pH/EC Sensor Integration Guide
## Adding EZO Sensors to Batch Dashboard

### Installation

1. **Install required package:**
```bash
pip3 install smbus2
```

2. **Copy the sensor script:**
```bash
cp ph_ec_simple.py /home/pi/batch-dashboard/hardware/
```

3. **Enable I2C on your Pi (if not already enabled):**
```bash
sudo raspi-config
# Navigate to: Interface Options > I2C > Enable
```

### Quick Test

Test the sensors directly:
```bash
cd /home/pi/batch-dashboard/hardware
python3 ph_ec_simple.py
```

### Flask API Integration

Add these endpoints to your `app.py`:

```python
from hardware.ph_ec_simple import PHECSensor

# Initialize in your app setup
ph_ec_sensor = PHECSensor()

# Add these routes:

@app.route('/api/sensors/ph-ec/connect', methods=['POST'])
def connect_ph_ec():
    """Connect to pH/EC sensors"""
    try:
        if ph_ec_sensor.connect():
            return jsonify({'success': True, 'message': 'Connected to sensors'})
        else:
            return jsonify({'success': False, 'message': 'Failed to connect'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/sensors/ph-ec/read', methods=['GET'])
def read_ph_ec():
    """Read current pH and EC values"""
    try:
        if not ph_ec_sensor.is_connected():
            return jsonify({'success': False, 'message': 'Not connected'}), 400
        
        readings = ph_ec_sensor.read_sensors()
        
        return jsonify({
            'success': True,
            'data': {
                'ph': readings['ph'],
                'ec': readings['ec'],
                'timestamp': readings['timestamp']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/sensors/ph-ec/status', methods=['GET'])
def get_ph_ec_status():
    """Get sensor info and calibration status"""
    try:
        if not ph_ec_sensor.is_connected():
            return jsonify({'success': False, 'message': 'Not connected'}), 400
        
        info = ph_ec_sensor.get_sensor_info()
        latest = ph_ec_sensor.get_latest_readings()
        
        return jsonify({
            'success': True,
            'connected': True,
            'sensors': info,
            'latest_readings': latest
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/sensors/ph/calibrate', methods=['POST'])
def calibrate_ph():
    """
    Calibrate pH sensor
    Body: {"point": "mid"|"low"|"high"|"clear", "value": 7.0 (optional)}
    """
    try:
        if not ph_ec_sensor.is_connected():
            return jsonify({'success': False, 'message': 'Not connected'}), 400
        
        data = request.get_json()
        point = data.get('point')
        value = data.get('value')
        
        if point == 'mid':
            result = ph_ec_sensor.calibrate_ph_mid(value)
        elif point == 'low':
            result = ph_ec_sensor.calibrate_ph_low(value)
        elif point == 'high':
            result = ph_ec_sensor.calibrate_ph_high(value)
        elif point == 'clear':
            result = ph_ec_sensor.clear_ph_calibration()
        else:
            return jsonify({'success': False, 'message': 'Invalid calibration point'}), 400
        
        if result:
            return jsonify({'success': True, 'message': f'pH {point} calibration successful'})
        else:
            return jsonify({'success': False, 'message': 'Calibration failed'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/sensors/ec/calibrate', methods=['POST'])
def calibrate_ec():
    """
    Calibrate EC sensor
    Body: {"point": "dry"|"single"|"low"|"high"|"clear", "value": 1413 (optional)}
    """
    try:
        if not ph_ec_sensor.is_connected():
            return jsonify({'success': False, 'message': 'Not connected'}), 400
        
        data = request.get_json()
        point = data.get('point')
        value = data.get('value')
        
        if point == 'dry':
            result = ph_ec_sensor.calibrate_ec_dry()
        elif point == 'single':
            result = ph_ec_sensor.calibrate_ec_single(value)
        elif point == 'low':
            result = ph_ec_sensor.calibrate_ec_low(value)
        elif point == 'high':
            result = ph_ec_sensor.calibrate_ec_high(value)
        elif point == 'clear':
            result = ph_ec_sensor.clear_ec_calibration()
        else:
            return jsonify({'success': False, 'message': 'Invalid calibration point'}), 400
        
        if result:
            return jsonify({'success': True, 'message': f'EC {point} calibration successful'})
        else:
            return jsonify({'success': False, 'message': 'Calibration failed'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
```

### Frontend Integration (Svelte)

Add these API calls to your Svelte components:

```javascript
// Read sensors
async function readSensors() {
    const response = await fetch('/api/sensors/ph-ec/read');
    const data = await response.json();
    if (data.success) {
        ph = data.data.ph;
        ec = data.data.ec;
    }
}

// pH calibration
async function calibratePH(point, value = null) {
    const response = await fetch('/api/sensors/ph/calibrate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ point, value })
    });
    const data = await response.json();
    return data;
}

// EC calibration
async function calibrateEC(point, value = null) {
    const response = await fetch('/api/sensors/ec/calibrate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ point, value })
    });
    const data = await response.json();
    return data;
}
```

### Usage Example

1. **Connect on startup** (add to your Flask app initialization):
```python
if __name__ == '__main__':
    # Connect to pH/EC sensors
    print("Connecting to pH/EC sensors...")
    if ph_ec_sensor.connect():
        print("✓ pH/EC sensors ready")
    else:
        print("⚠ pH/EC sensors not available")
    
    app.run(host='0.0.0.0', port=5000)
```

2. **Read in your mixing logic**:
```python
# During mixing, check pH/EC
readings = ph_ec_sensor.read_sensors()
current_ph = readings['ph']
current_ec = readings['ec']

if current_ph and current_ph < target_ph:
    # Adjust pH
    pass
```

### Calibration Workflow

**pH Calibration (3-point recommended):**
1. Clean probe with distilled water
2. Place in pH 7.0 buffer → call `calibrate_ph_mid(7.0)`
3. Rinse, place in pH 4.0 buffer → call `calibrate_ph_low(4.0)`
4. Rinse, place in pH 10.0 buffer → call `calibrate_ph_high(10.0)`

**EC Calibration (2-point recommended):**
1. Clean probe, dry completely
2. In air → call `calibrate_ec_dry()`
3. Place in 1413 μS/cm solution → call `calibrate_ec_high(1413)`

**Single-point EC (faster but less accurate):**
1. Clean probe, dry completely
2. In air → call `calibrate_ec_dry()`
3. Place in 1413 μS/cm solution → call `calibrate_ec_single(1413)`

### Troubleshooting

**"Failed to connect":**
- Check I2C is enabled: `ls /dev/i2c-*`
- Verify addresses: `i2cdetect -y 1`
- Should see devices at 0x63 (pH) and 0x64 (EC)

**"Invalid reading":**
- Check probe connections
- Verify probes are in liquid (not air)
- Check calibration status

**"Calibration failed":**
- Make sure probe is stable in calibration solution
- Wait 30 seconds before calibrating
- Verify solution values are correct
