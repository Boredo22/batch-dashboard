# =============================================================================
# PART 1: Enhanced hardware_comms.py additions
# Add these methods to the HardwareComms class in hardware_comms.py
# =============================================================================

def calibrate_pump(self, pump_id: int, actual_volume_ml: float) -> bool:
    """
    Calibrate EZO pump with actual dispensed volume
    
    Args:
        pump_id: Pump ID
        actual_volume_ml: The actual volume that was measured
    
    Returns:
        bool: Success status
    """
    from hardware.rpi_pumps import EZOPumpController
    
    try:
        # Create pump controller instance
        pump_controller = EZOPumpController()
        
        # Send calibration command (Cal,{actual_volume})
        success = pump_controller.calibrate_pump(pump_id, actual_volume_ml)
        
        # Clean up
        pump_controller.close()
        
        if success:
            pump_name = get_pump_name(pump_id)
            logger.info(f"Calibrated {pump_name} with {actual_volume_ml}ml")
        else:
            logger.error(f"Failed to calibrate pump {pump_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Exception calibrating pump {pump_id}: {e}")
        return False

def clear_pump_calibration(self, pump_id: int) -> bool:
    """
    Clear EZO pump calibration data
    
    Args:
        pump_id: Pump ID
    
    Returns:
        bool: Success status
    """
    from hardware.rpi_pumps import EZOPumpController
    
    try:
        pump_controller = EZOPumpController()
        
        # Send Cal,clear command
        response = pump_controller.send_command(pump_id, "Cal,clear")
        success = response is not None
        
        pump_controller.close()
        
        if success:
            pump_name = get_pump_name(pump_id)
            logger.info(f"Cleared calibration for {pump_name}")
        
        return success
        
    except Exception as e:
        logger.error(f"Exception clearing pump {pump_id} calibration: {e}")
        return False

def check_pump_calibration_status(self, pump_id: int) -> dict:
    """
    Check EZO pump calibration status
    
    Args:
        pump_id: Pump ID
    
    Returns:
        dict: Calibration status info
    """
    from hardware.rpi_pumps import EZOPumpController
    
    try:
        pump_controller = EZOPumpController()
        
        # Send Cal,? command to check calibration status
        response = pump_controller.send_command(pump_id, "Cal,?")
        
        pump_controller.close()
        
        if response:
            # Parse response: ?Cal,0=uncalibrated, ?Cal,1=single point, ?Cal,2=volume, ?Cal,3=both
            if response.startswith("?Cal,"):
                cal_status = response.split(",")[1] if "," in response else "0"
                status_map = {
                    "0": "uncalibrated",
                    "1": "single_point",
                    "2": "volume_calibrated", 
                    "3": "fully_calibrated"
                }
                
                return {
                    'success': True,
                    'pump_id': pump_id,
                    'calibration_status': status_map.get(cal_status, "unknown"),
                    'raw_response': response
                }
        
        return {
            'success': False,
            'pump_id': pump_id,
            'calibration_status': 'unknown',
            'error': 'Failed to get calibration status'
        }
        
    except Exception as e:
        logger.error(f"Exception checking pump {pump_id} calibration: {e}")
        return {
            'success': False,
            'pump_id': pump_id,
            'error': str(e)
        }

def pause_pump(self, pump_id: int) -> bool:
    """
    Pause EZO pump during dispensing
    
    Args:
        pump_id: Pump ID
    
    Returns:
        bool: Success status
    """
    from hardware.rpi_pumps import EZOPumpController
    
    try:
        pump_controller = EZOPumpController()
        
        # Send P command to pause
        response = pump_controller.send_command(pump_id, "P")
        success = response is not None
        
        pump_controller.close()
        
        if success:
            pump_name = get_pump_name(pump_id)
            logger.info(f"Paused {pump_name}")
        
        return success
        
    except Exception as e:
        logger.error(f"Exception pausing pump {pump_id}: {e}")
        return False

def get_pump_voltage(self, pump_id: int) -> dict:
    """
    Get EZO pump voltage
    
    Args:
        pump_id: Pump ID
    
    Returns:
        dict: Voltage info
    """
    from hardware.rpi_pumps import EZOPumpController
    
    try:
        pump_controller = EZOPumpController()
        
        # Send PV,? command to get voltage
        response = pump_controller.send_command(pump_id, "PV,?")
        
        pump_controller.close()
        
        if response and response.startswith("?PV,"):
            voltage_str = response.split(",")[1] if "," in response else "0"
            try:
                voltage = float(voltage_str)
                return {
                    'success': True,
                    'pump_id': pump_id,
                    'voltage': voltage,
                    'raw_response': response
                }
            except ValueError:
                pass
        
        return {
            'success': False,
            'pump_id': pump_id,
            'error': 'Failed to get voltage'
        }
        
    except Exception as e:
        logger.error(f"Exception getting pump {pump_id} voltage: {e}")
        return {
            'success': False,
            'pump_id': pump_id,
            'error': str(e)
        }

def get_current_dispensed_volume(self, pump_id: int) -> dict:
    """
    Get current dispensed volume from EZO pump
    
    Args:
        pump_id: Pump ID
    
    Returns:
        dict: Volume info
    """
    from hardware.rpi_pumps import EZOPumpController
    
    try:
        pump_controller = EZOPumpController()
        
        # Send R command to read current volume
        response = pump_controller.send_command(pump_id, "R")
        
        pump_controller.close()
        
        if response:
            try:
                volume = float(response)
                return {
                    'success': True,
                    'pump_id': pump_id,
                    'current_volume': volume,
                    'raw_response': response
                }
            except ValueError:
                pass
        
        return {
            'success': False,
            'pump_id': pump_id,
            'error': 'Failed to get current volume'
        }
        
    except Exception as e:
        logger.error(f"Exception getting pump {pump_id} current volume: {e}")
        return {
            'success': False,
            'pump_id': pump_id,
            'error': str(e)
        }

# =============================================================================
# PART 2: Add convenience functions at bottom of hardware_comms.py
# =============================================================================

def calibrate_pump(pump_id: int, actual_volume_ml: float) -> bool:
    """Calibrate pump - convenience function"""
    return get_hardware_comms().calibrate_pump(pump_id, actual_volume_ml)

def clear_pump_calibration(pump_id: int) -> bool:
    """Clear pump calibration - convenience function"""
    return get_hardware_comms().clear_pump_calibration(pump_id)

def check_pump_calibration_status(pump_id: int) -> dict:
    """Check pump calibration status - convenience function"""
    return get_hardware_comms().check_pump_calibration_status(pump_id)

def pause_pump(pump_id: int) -> bool:
    """Pause pump - convenience function"""
    return get_hardware_comms().pause_pump(pump_id)

def get_pump_voltage(pump_id: int) -> dict:
    """Get pump voltage - convenience function"""
    return get_hardware_comms().get_pump_voltage(pump_id)

def get_current_dispensed_volume(pump_id: int) -> dict:
    """Get current dispensed volume - convenience function"""
    return get_hardware_comms().get_current_dispensed_volume(pump_id)

# =============================================================================
# PART 3: Fixed and enhanced Flask API endpoints in app.py
# =============================================================================

@app.route('/api/pumps/<int:pump_id>/calibrate', methods=['POST'])
def api_calibrate_pump(pump_id):
    """Calibrate pump with actual measured volume"""
    try:
        data = request.get_json() or {}
        target_volume = float(data.get('target_volume', 0))
        actual_volume = float(data.get('actual_volume', 0))
        
        if not target_volume or not actual_volume:
            return jsonify({
                'success': False,
                'error': 'Both target_volume and actual_volume parameters required'
            }), 400
        
        if target_volume <= 0 or actual_volume <= 0:
            return jsonify({
                'success': False,
                'error': 'Volumes must be greater than 0'
            }), 400
        
        # Calculate calibration factor for logging
        calibration_factor = actual_volume / target_volume
        
        # Log the calibration for debugging
        logger.info(f"Calibrating pump {pump_id}: target={target_volume}ml, actual={actual_volume}ml, factor={calibration_factor:.4f}")
        
        # FIXED: Actually calibrate the pump using hardware_comms
        from hardware.hardware_comms import calibrate_pump
        
        success = calibrate_pump(pump_id, actual_volume)
        
        return jsonify({
            'success': success,
            'pump_id': pump_id,
            'target_volume': target_volume,
            'actual_volume': actual_volume,
            'calibration_factor': calibration_factor,
            'message': f"Pump {pump_id} calibrated successfully (factor: {calibration_factor:.4f})" if success else "Calibration failed - check logs"
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid volume values: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error calibrating pump {pump_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pumps/<int:pump_id>/calibration/clear', methods=['POST'])
def api_clear_pump_calibration(pump_id):
    """Clear pump calibration data"""
    try:
        from hardware.hardware_comms import clear_pump_calibration
        
        success = clear_pump_calibration(pump_id)
        
        return jsonify({
            'success': success,
            'pump_id': pump_id,
            'message': f"Pump {pump_id} calibration cleared" if success else "Failed to clear calibration"
        })
        
    except Exception as e:
        logger.error(f"Error clearing pump {pump_id} calibration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pumps/<int:pump_id>/calibration/status', methods=['GET'])
def api_check_pump_calibration_status(pump_id):
    """Check pump calibration status"""
    try:
        from hardware.hardware_comms import check_pump_calibration_status
        
        result = check_pump_calibration_status(pump_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error checking pump {pump_id} calibration status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pumps/<int:pump_id>/pause', methods=['POST'])
def api_pause_pump(pump_id):
    """Pause pump during dispensing"""
    try:
        from hardware.hardware_comms import pause_pump
        
        success = pause_pump(pump_id)
        
        return jsonify({
            'success': success,
            'pump_id': pump_id,
            'message': f"Pump {pump_id} paused" if success else "Failed to pause pump"
        })
        
    except Exception as e:
        logger.error(f"Error pausing pump {pump_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pumps/<int:pump_id>/status', methods=['GET'])
def api_get_pump_status(pump_id):
    """Get comprehensive pump status including voltage, calibration, and current volume"""
    try:
        from hardware.hardware_comms import (
            get_pump_voltage, 
            check_pump_calibration_status,
            get_current_dispensed_volume
        )
        
        # Get all status info
        voltage_info = get_pump_voltage(pump_id)
        calibration_info = check_pump_calibration_status(pump_id)
        volume_info = get_current_dispensed_volume(pump_id)
        
        pump_name = get_pump_name(pump_id)
        
        return jsonify({
            'success': True,
            'pump_id': pump_id,
            'pump_name': pump_name,
            'voltage': voltage_info,
            'calibration': calibration_info,
            'current_volume': volume_info
        })
        
    except Exception as e:
        logger.error(f"Error getting pump {pump_id} status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pumps/<int:pump_id>/volume', methods=['GET'])
def api_get_current_volume(pump_id):
    """Get current dispensed volume from pump"""
    try:
        from hardware.hardware_comms import get_current_dispensed_volume
        
        result = get_current_dispensed_volume(pump_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting pump {pump_id} current volume: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# PART 4: Enhanced Svelte frontend component improvements
# Add these features to PumpCalibration.svelte
# =============================================================================

/*
Enhanced PumpCalibration.svelte additions:

1. Add calibration status checking before starting calibration
2. Add ability to clear calibration
3. Add real-time volume monitoring during dispensing
4. Add pause/resume functionality
5. Better error handling and user feedback

Add these reactive statements and functions:

let calibrationStatusInfo = $state(null);
let isCheckingStatus = $state(false);
let currentVolumeInfo = $state(null);
let volumeCheckInterval = $state(null);

// Check calibration status
async function checkCalibrationStatus() {
  isCheckingStatus = true;
  try {
    const response = await fetch(`/api/pumps/${selectedPumpNumber}/calibration/status`);
    const data = await response.json();
    calibrationStatusInfo = data;
  } catch (error) {
    statusMessage = `Error checking calibration status: ${error.message}`;
  }
  isCheckingStatus = false;
}

// Clear calibration
async function clearCalibration() {
  try {
    const response = await fetch(`/api/pumps/${selectedPumpNumber}/calibration/clear`, {
      method: 'POST'
    });
    
    if (response.ok) {
      statusMessage = 'Calibration cleared successfully';
      await checkCalibrationStatus();
    } else {
      throw new Error('Failed to clear calibration');
    }
  } catch (error) {
    statusMessage = `Error clearing calibration: ${error.message}`;
  }
}

// Monitor current volume during dispensing
function startVolumeMonitoring() {
  if (volumeCheckInterval) clearInterval(volumeCheckInterval);
  
  volumeCheckInterval = setInterval(async () => {
    try {
      const response = await fetch(`/api/pumps/${selectedPumpNumber}/volume`);
      const data = await response.json();
      currentVolumeInfo = data;
    } catch (error) {
      console.error('Error monitoring volume:', error);
    }
  }, 1000);
}

function stopVolumeMonitoring() {
  if (volumeCheckInterval) {
    clearInterval(volumeCheckInterval);
    volumeCheckInterval = null;
  }
}

// Pause pump
async function pausePump() {
  try {
    const response = await fetch(`/api/pumps/${selectedPumpNumber}/pause`, {
      method: 'POST'
    });
    
    if (response.ok) {
      statusMessage = 'Pump paused - dispense same command again to resume';
    } else {
      throw new Error('Failed to pause pump');
    }
  } catch (error) {
    statusMessage = `Error pausing pump: ${error.message}`;
  }
}

// Call checkCalibrationStatus when component mounts or pump changes
$effect(() => {
  if (selectedPumpNumber) {
    checkCalibrationStatus();
  }
});

// Clean up interval on component unmount
$effect(() => {
  return () => {
    stopVolumeMonitoring();
  };
});
*/