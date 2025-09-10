# Fix Pump Calibration Checks - Claude Code Instructions

## Problem Analysis
From the logs, the system is repeatedly checking pump calibration status every time the nutrients page is accessed, causing:
- Multiple `NO_DATA` errors 
- Slow page loading
- Unnecessary I2C bus operations
- System instability

## Required Changes

### 1. Modify Hardware Initialization (hardware/rpi_pumps.py)

**Current Issue:** Calibration status is checked every time pumps are accessed

**Fix:** Check calibration status once during initialization and cache results

```python
class RPiPumps:
    def __init__(self):
        self.pumps = {}
        self.calibration_status = {}  # Add this cache
        # ... existing initialization
        
    def initialize_pumps(self):
        """Initialize pumps and check calibration once"""
        # ... existing pump initialization code
        
        # After successful pump initialization, check calibration once
        self._check_all_calibrations()
        
    def _check_all_calibrations(self):
        """Check calibration status for all pumps once and cache results"""
        logger.info("Checking pump calibration status...")
        
        for pump_id in range(1, 9):  # Pumps 1-8
            try:
                # Check calibration status
                cal_response = self._send_command(pump_id, "CAL,?")
                if cal_response and "CAL" in cal_response:
                    # Parse calibration status (0=uncalibrated, 1=single point, 2=dual point)
                    cal_status = int(cal_response.split(',')[1]) if ',' in cal_response else 0
                    self.calibration_status[pump_id] = cal_status
                    logger.info(f"Pump {pump_id}: Calibration status {cal_status}")
                else:
                    self.calibration_status[pump_id] = 0  # Default to uncalibrated
                    logger.warning(f"Pump {pump_id}: Could not read calibration status")
                    
            except Exception as e:
                logger.error(f"Error checking calibration for pump {pump_id}: {e}")
                self.calibration_status[pump_id] = 0  # Default to uncalibrated
                
        logger.info("Calibration status check completed")
        
    def get_calibration_status(self, pump_id):
        """Get cached calibration status"""
        return self.calibration_status.get(pump_id, 0)
        
    def is_calibrated(self, pump_id):
        """Check if pump is calibrated (cached)"""
        return self.get_calibration_status(pump_id) > 0
```

### 2. Update Main Hardware Communications (hardware/hardware_comms.py)

**Fix:** Remove repeated calibration checks from status methods

```python
def get_pump_status(self, pump_id=None):
    """Get pump status without rechecking calibration"""
    if pump_id:
        # Return single pump status using cached calibration
        pump_info = self.pumps.get_pump_info(pump_id)
        return {
            'id': pump_id,
            'name': pump_info.get('name', f'Pump {pump_id}'),
            'voltage': pump_info.get('voltage', 0),
            'calibrated': self.pumps.is_calibrated(pump_id),  # Use cached status
            'status': 'ready' if self.pumps.is_calibrated(pump_id) else 'uncalibrated'
        }
    else:
        # Return all pump statuses using cached calibration
        statuses = {}
        for pid in range(1, 9):
            statuses[pid] = self.get_pump_status(pid)
        return statuses
```

### 3. Update Web Routes (app.py or routes)

**Fix:** Remove calibration checks from page load routes

```python
@app.route('/nutrients')
def nutrients_page():
    """Nutrients page - use cached pump status"""
    try:
        # Get pump statuses (using cached calibration data)
        pump_statuses = hardware_comm.get_pump_status()
        
        # No need to re-check calibration here
        return render_template('nutrients.html', 
                             pumps=pump_statuses,
                             system_ready=True)
                             
    except Exception as e:
        logger.error(f"Error loading nutrients page: {e}")
        return render_template('nutrients.html', 
                             error="System not ready",
                             system_ready=False)

@app.route('/api/pump/status')
def api_pump_status():
    """API endpoint for pump status - no calibration recheck"""
    try:
        statuses = hardware_comm.get_pump_status()
        return jsonify(statuses)
    except Exception as e:
        logger.error(f"Error getting pump status: {e}")
        return jsonify({'error': str(e)}), 500
```

### 4. Add Manual Calibration Refresh (Optional)

**Add:** Manual calibration recheck for maintenance

```python
@app.route('/api/pump/refresh-calibration', methods=['POST'])
def refresh_calibration():
    """Manually refresh calibration status for all pumps"""
    try:
        hardware_comm.pumps._check_all_calibrations()
        return jsonify({'success': True, 'message': 'Calibration status refreshed'})
    except Exception as e:
        logger.error(f"Error refreshing calibration: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pump/<int:pump_id>/calibrate', methods=['POST'])
def calibrate_pump(pump_id):
    """Calibrate a specific pump and update cache"""
    try:
        # Perform calibration
        result = hardware_comm.calibrate_pump(pump_id)
        
        # Update cached calibration status
        hardware_comm.pumps._check_all_calibrations()
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error calibrating pump {pump_id}: {e}")
        return jsonify({'error': str(e)}), 500
```

### 5. Update Startup Sequence (main.py or app.py)

**Fix:** Ensure calibration check happens once during startup

```python
def initialize_hardware():
    """Initialize hardware with single calibration check"""
    try:
        logger.info("Starting hardware initialization...")
        
        # Initialize pump controller (includes calibration check)
        feed_control.initialize_pumps()  # This now includes calibration check
        logger.info("✓ EZO pump controller initialized with calibration status")
        
        # Initialize other hardware...
        # ... existing initialization code
        
        logger.info("Hardware initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Hardware initialization failed: {e}")
        return False
```

## Implementation Steps

1. **Backup Current Code:**
   ```bash
   git add -A && git commit -m "Backup before calibration fix"
   ```

2. **Apply Changes in Order:**
   - First: Update `hardware/rpi_pumps.py` with calibration caching
   - Second: Update `hardware/hardware_comms.py` to use cached status
   - Third: Update web routes to remove repeated checks
   - Fourth: Test the system

3. **Test the Fix:**
   - Start the Flask app and verify single calibration check in logs
   - Load nutrients page multiple times - should be fast with no repeated checks
   - Verify pump status is still accurate

4. **Verification:**
   - Look for single "Checking pump calibration status..." message at startup
   - No more "NO_DATA" errors when loading nutrients page
   - Faster page loading times
   - System remains stable

## Benefits

- **Performance:** Eliminates repeated I2C bus operations
- **Reliability:** Reduces "NO_DATA" errors
- **Speed:** Faster page loading
- **Maintainability:** Clear separation of initialization vs runtime operations
- **Flexibility:** Manual calibration refresh when needed

## Rollback Plan

If issues occur:
```bash
git reset --hard HEAD~1
```

This will restore the previous working state while you debug any issues.