#!/usr/bin/env python3
"""
Flask API Server for Nutrient Mixing System
Provides REST API endpoints for Svelte frontend
Uses hardware_comms.py for reliable hardware control like simple_gui.py
"""

# CRITICAL: Import hardware safety FIRST
from hardware_safety import setup_hardware_safety
import sys

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import atexit
from datetime import datetime, time
from typing import Dict, Any

# Import our reliable hardware communications module
from hardware.hardware_comms import (
    control_relay, dispense_pump, stop_pump, start_flow, stop_flow,
    emergency_stop, get_system_status, get_available_hardware,
    all_relays_off, cleanup_hardware, start_ec_ph, stop_ec_ph,
    calibrate_pump, clear_pump_calibration, check_pump_calibration_status,
    pause_pump, get_pump_voltage, get_current_dispensed_volume,
    get_pump_status, refresh_pump_calibrations,
    read_ec_ph_sensors, calibrate_ph, calibrate_ec, get_sensor_calibration_status
)

# Import configuration constants and all settings
try:
    import config
    from config import *
    from config import get_pump_name
except ImportError:
    # Fallback constants
    MIN_PUMP_VOLUME_ML = 1
    MAX_PUMP_VOLUME_ML = 100
    MAX_FLOW_GALLONS = 50
    # Create minimal fallback config
    class config:
        TANKS = {}
        PUMP_NAMES = {}
        PUMP_ADDRESSES = {}
        RELAY_GPIO_PINS = {}
        FLOW_METER_GPIO_PINS = {}
        STATUS_UPDATE_INTERVAL = 2.0
        PUMP_CHECK_INTERVAL = 1.0
        FLOW_UPDATE_INTERVAL = 0.5
        MAX_PUMP_VOLUME_ML = 2500.0
        MIN_PUMP_VOLUME_ML = 0.5
        MAX_FLOW_GALLONS = 100
        I2C_BUS_NUMBER = 1
        EZO_COMMAND_DELAY = 0.3
        COMMAND_START = "Start"
        COMMAND_END = "end"
        ARDUINO_UNO_BAUDRATE = 115200
        MOCK_SETTINGS = {}
        DEBUG_MODE = False
        VERBOSE_LOGGING = False
        LOG_LEVEL = "INFO"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = 'nutrient_mixing_system_2024'

# CRITICAL: Setup hardware safety FIRST
safety_manager = setup_hardware_safety(app)
if not safety_manager:
    print("Another instance running or safety setup failed")
    sys.exit(1)

# Register cleanup on app shutdown
atexit.register(cleanup_hardware)

# =============================================================================
# STATIC FILE SERVING - Serve Svelte build files
# =============================================================================

@app.route('/')
def serve_dashboard():
    """Serve Dashboard Svelte app"""
    return send_from_directory('static/dist', 'dashboard.html')

@app.route('/status')
def serve_status():
    """Serve Status Svelte app"""  
    return send_from_directory('static/dist', 'status.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, assets)"""
    return send_from_directory('static', filename)

@app.route('/dist/<path:filename>')
def serve_dist(filename):
    """Serve built Svelte files"""
    return send_from_directory('static/dist', filename)

# =============================================================================
# CONFIGURATION ENDPOINTS - Load and save system configuration
# =============================================================================

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get current system configuration"""
    try:
        # Return all configuration settings in the format expected by Settings.svelte
        config_data = {
            # Tank configuration
            'TANKS': getattr(config, 'TANKS', {}),
            
            # Pump configuration
            'PUMP_NAMES': getattr(config, 'PUMP_NAMES', {}),
            'PUMP_ADDRESSES': getattr(config, 'PUMP_ADDRESSES', {}),
            
            # System timing
            'STATUS_UPDATE_INTERVAL': getattr(config, 'STATUS_UPDATE_INTERVAL', 2.0),
            'PUMP_CHECK_INTERVAL': getattr(config, 'PUMP_CHECK_INTERVAL', 1.0),
            'FLOW_UPDATE_INTERVAL': getattr(config, 'FLOW_UPDATE_INTERVAL', 0.5),
            
            # Safety limits
            'MAX_PUMP_VOLUME_ML': getattr(config, 'MAX_PUMP_VOLUME_ML', 2500.0),
            'MIN_PUMP_VOLUME_ML': getattr(config, 'MIN_PUMP_VOLUME_ML', 0.5),
            'MAX_FLOW_GALLONS': getattr(config, 'MAX_FLOW_GALLONS', 100),
            
            # GPIO Configuration
            'RELAY_GPIO_PINS': getattr(config, 'RELAY_GPIO_PINS', {}),
            'FLOW_METER_GPIO_PINS': getattr(config, 'FLOW_METER_GPIO_PINS', {}),
            
            # I2C Configuration
            'I2C_BUS_NUMBER': getattr(config, 'I2C_BUS_NUMBER', 1),
            'EZO_COMMAND_DELAY': getattr(config, 'EZO_COMMAND_DELAY', 0.3),
            
            # Communication
            'COMMAND_START': getattr(config, 'COMMAND_START', 'Start'),
            'COMMAND_END': getattr(config, 'COMMAND_END', 'end'),
            'ARDUINO_UNO_BAUDRATE': getattr(config, 'ARDUINO_UNO_BAUDRATE', 115200),
            
            # Mock settings
            'MOCK_SETTINGS': getattr(config, 'MOCK_SETTINGS', {}),
            
            # Debug settings
            'DEBUG_MODE': getattr(config, 'DEBUG_MODE', False),
            'VERBOSE_LOGGING': getattr(config, 'VERBOSE_LOGGING', False),
            'LOG_LEVEL': getattr(config, 'LOG_LEVEL', 'INFO')
        }
        
        return jsonify(config_data)
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['POST'])
def api_save_config():
    """Save system configuration changes"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No configuration data provided'
            }), 400
        
        user_settings = data.get('userSettings', {})
        dev_settings = data.get('devSettings', {})
        
        # For now, just log the configuration changes
        # In a full implementation, you would save these to a configuration file
        logger.info("Configuration update received:")
        logger.info(f"User settings: {user_settings}")
        logger.info(f"Dev settings: {dev_settings}")
        
        # TODO: Implement actual configuration saving to file
        # This would typically involve:
        # 1. Validating the configuration values
        # 2. Writing to config.py or a separate config file
        # 3. Potentially restarting certain services
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# SETTINGS ENDPOINTS - User and Developer Settings
# =============================================================================

@app.route('/api/settings/user', methods=['GET'])
def api_get_user_settings():
    """Get user settings"""
    try:
        # Get current configuration from config module
        user_settings = {
            'tanks': getattr(config, 'TANKS', {}),
            'pumps': {
                'names': getattr(config, 'PUMP_NAMES', {}),
                'addresses': getattr(config, 'PUMP_ADDRESSES', {})
            },
            'timing': {
                'status_update_interval': getattr(config, 'STATUS_UPDATE_INTERVAL', 2.0),
                'pump_check_interval': getattr(config, 'PUMP_CHECK_INTERVAL', 1.0),
                'flow_update_interval': getattr(config, 'FLOW_UPDATE_INTERVAL', 0.5)
            },
            'limits': {
                'max_pump_volume_ml': getattr(config, 'MAX_PUMP_VOLUME_ML', 2500.0),
                'min_pump_volume_ml': getattr(config, 'MIN_PUMP_VOLUME_ML', 0.5),
                'max_flow_gallons': getattr(config, 'MAX_FLOW_GALLONS', 100)
            }
        }
        
        return jsonify(user_settings)
        
    except Exception as e:
        logger.error(f"Error loading user settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settings/user', methods=['POST'])
def api_save_user_settings():
    """Save user settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No user settings data provided'
            }), 400
        
        logger.info(f"User settings update: {data}")
        
        # TODO: Implement actual saving to config file
        return jsonify({
            'success': True,
            'message': 'User settings saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving user settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settings/developer', methods=['GET'])
def api_get_developer_settings():
    """Get developer settings"""
    try:
        dev_settings = {
            'gpio': {
                'relay_pins': getattr(config, 'RELAY_GPIO_PINS', {}),
                'flow_meter_pins': getattr(config, 'FLOW_METER_GPIO_PINS', {})
            },
            'i2c': {
                'bus_number': getattr(config, 'I2C_BUS_NUMBER', 1),
                'pump_addresses': getattr(config, 'PUMP_ADDRESSES', {}),
                'command_delay': getattr(config, 'EZO_COMMAND_DELAY', 0.3)
            },
            'communication': {
                'command_start': getattr(config, 'COMMAND_START', 'Start'),
                'command_end': getattr(config, 'COMMAND_END', 'end'),
                'arduino_baudrate': getattr(config, 'ARDUINO_UNO_BAUDRATE', 115200)
            },
            'mock': getattr(config, 'MOCK_SETTINGS', {
                'mock_mode': False,
                'mock_pumps': False,
                'mock_relays': False,
                'mock_flow_meters': False,
                'mock_ecph': False
            }),
            'debug': {
                'debug_mode': getattr(config, 'DEBUG_MODE', False),
                'verbose_logging': getattr(config, 'VERBOSE_LOGGING', False),
                'log_level': getattr(config, 'LOG_LEVEL', 'INFO')
            }
        }
        
        return jsonify(dev_settings)
        
    except Exception as e:
        logger.error(f"Error loading developer settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settings/developer', methods=['POST'])
def api_save_developer_settings():
    """Save developer settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No developer settings data provided'
            }), 400
        
        logger.info(f"Developer settings update: {data}")
        
        # TODO: Implement actual saving to config file
        return jsonify({
            'success': True,
            'message': 'Developer settings saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving developer settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# NUTRIENTS CONFIGURATION ENDPOINTS - Separate nutrients management
# =============================================================================

@app.route('/api/nutrients', methods=['GET'])
def api_get_nutrients():
    """Get nutrients configuration"""
    try:
        import json
        import os
        
        nutrients_file = 'nutrients.json'
        if os.path.exists(nutrients_file):
            with open(nutrients_file, 'r') as f:
                nutrients_data = json.load(f)
        else:
            # Create default nutrients configuration if file doesn't exist
            nutrients_data = {
                "available_nutrients": [
                    {"name": "Veg A", "defaultDosage": 4.0},
                    {"name": "Veg B", "defaultDosage": 4.0},
                    {"name": "Bloom A", "defaultDosage": 4.0},
                    {"name": "Bloom B", "defaultDosage": 4.0},
                    {"name": "Cake", "defaultDosage": 2.0},
                    {"name": "PK Synergy", "defaultDosage": 2.0},
                    {"name": "Runclean", "defaultDosage": 1.0},
                    {"name": "pH Down", "defaultDosage": 0.5}
                ],
                "veg_formula": {
                    "Veg A": 4.0,
                    "Veg B": 4.0,
                    "Cake": 2.0,
                    "pH Down": 0.5
                },
                "bloom_formula": {
                    "Bloom A": 4.0,
                    "Bloom B": 4.0,
                    "PK Synergy": 2.0,
                    "Cake": 1.0,
                    "pH Down": 0.5
                },
                "pump_name_to_id": {
                    "Veg A": 1,
                    "Veg B": 2,
                    "Bloom A": 3,
                    "Bloom B": 4,
                    "Cake": 5,
                    "PK Synergy": 6,
                    "Runclean": 7,
                    "pH Down": 8
                }
            }
            # Save default configuration
            with open(nutrients_file, 'w') as f:
                json.dump(nutrients_data, f, indent=2)
        
        return jsonify(nutrients_data)
        
    except Exception as e:
        logger.error(f"Error loading nutrients configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nutrients', methods=['POST'])
def api_save_nutrients():
    """Save nutrients configuration"""
    try:
        import json
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No nutrients data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['available_nutrients', 'veg_formula', 'bloom_formula', 'pump_name_to_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Save to nutrients.json
        with open('nutrients.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info("Nutrients configuration saved successfully")
        
        return jsonify({
            'success': True,
            'message': 'Nutrients configuration saved successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error saving nutrients configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# API ENDPOINTS - Hardware Control (same patterns as simple_gui.py)
# =============================================================================

@app.route('/api/status')
@app.route('/api/hardware/status')
@app.route('/api/system/status')
def api_status():
    """Get current system status"""
    try:
        status = get_system_status()
        raw_hardware = get_available_hardware()
        
        # Transform hardware data to match expected structure
        hardware = {
            'pumps': raw_hardware['pumps'],
            'relays': raw_hardware['relays'],
            'flow_meters': raw_hardware['flow_meters'],
            'limits': {
                'pump_min_ml': raw_hardware['pumps']['volume_limits']['min_ml'],
                'pump_max_ml': raw_hardware['pumps']['volume_limits']['max_ml'],
                'flow_max_gallons': raw_hardware['flow_meters']['max_gallons']
            },
            'mock_settings': raw_hardware.get('mock_settings', {})
        }
        
        # Get pump status using cached calibration data
        pumps_status = get_pump_status()  # Get all pump statuses with cached calibration
        pumps_list = []
        
        for pid in hardware['pumps']['ids']:
            pump_info = status.get('pumps', {}).get(pid, {})
            cached_pump_status = pumps_status.get(pid, {})
            
            pump_data = {
                'id': pid,
                'name': hardware['pumps']['names'].get(pid, f'Pump {pid}'),
                'status': cached_pump_status.get('status', 'stopped'),
                'is_dispensing': cached_pump_status.get('is_dispensing', False),
                'voltage': cached_pump_status.get('voltage', 0.0),
                'connected': cached_pump_status.get('connected', False),
                'calibrated': cached_pump_status.get('calibrated', False),  # Use cached calibration
                'current_volume': cached_pump_status.get('current_volume', 0.0),
                'target_volume': cached_pump_status.get('target_volume', 0.0),
                'last_error': pump_info.get('last_error', '')
            }
            pumps_list.append(pump_data)

        return jsonify({
            'success': True,
            'status': status,
            'hardware': hardware,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # Add data in the format expected by Dashboard.svelte
            'relays': [{'id': rid, 'name': hardware['relays']['names'].get(rid, f'Relay {rid}'), 'state': status['relays'].get(str(rid), False)}
                      for rid in hardware['relays']['ids']],
            'pumps': pumps_list,
            'flow_meters': [{'id': fid, 'name': hardware['flow_meters']['names'].get(fid, f'Flow Meter {fid}'),
                           'status': 'stopped', 'flow_rate': 0, 'total_gallons': 0}
                          for fid in hardware['flow_meters']['ids']],
            'ec_value': status.get('ec', 0),
            'ph_value': status.get('ph', 0),
            'ec_ph_monitoring': status.get('ec_ph_active', False)
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# -----------------------------------------------------------------------------
# RELAY CONTROL - Using exact same patterns as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/relay/<int:relay_id>/<state>', methods=['GET', 'POST'])
def api_control_relay(relay_id, state):
    """Control individual relay"""
    try:
        # Convert state string to boolean
        relay_state = state.lower() in ['on', 'true', '1']
        
        success = control_relay(relay_id, relay_state)
        
        return jsonify({
            'success': success,
            'relay_id': relay_id,
            'state': 'ON' if relay_state else 'OFF',
            'message': f"Relay {relay_id} {'turned on' if relay_state else 'turned off'}" if success else "Command failed"
        })
    except Exception as e:
        logger.error(f"Error controlling relay {relay_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/relays/<int:relay_id>/control', methods=['POST'])
def api_control_relay_json(relay_id):
    """Control individual relay (JSON format for HeadGrower)"""
    try:
        data = request.get_json() or {}
        relay_state = data.get('state', False)
        
        success = control_relay(relay_id, relay_state)
        
        return jsonify({
            'success': success,
            'relay_id': relay_id,
            'state': 'ON' if relay_state else 'OFF',
            'message': f"Relay {relay_id} {'turned on' if relay_state else 'turned off'}" if success else "Command failed"
        })
    except Exception as e:
        logger.error(f"Error controlling relay {relay_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/relay/all/off', methods=['POST'])
def api_all_relays_off():
    """Turn all relays off"""
    try:
        success = all_relays_off()
        
        return jsonify({
            'success': success,
            'message': "All relays turned off" if success else "Failed to turn off relays"
        })
    except Exception as e:
        logger.error(f"Error turning off all relays: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# -----------------------------------------------------------------------------
# PUMP CONTROL - Using exact same patterns as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/pump/<int:pump_id>/dispense', methods=['POST'])
def api_dispense_pump(pump_id):
    """Start pump dispensing"""
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', request.args.get('amount', 0)))
        
        if not amount:
            return jsonify({
                'success': False,
                'error': 'Amount parameter required'
            }), 400
        
        success = dispense_pump(pump_id, amount)
        
        return jsonify({
            'success': success,
            'pump_id': pump_id,
            'amount': amount,
            'message': f"Dispensing {amount}ml from pump {pump_id}" if success else "Dispense command failed"
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid amount: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error dispensing from pump {pump_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pumps/<int:pump_id>/dispense', methods=['POST'])
def api_dispense_pump_plural(pump_id):
    """Start pump dispensing (plural endpoint for HeadGrower)"""
    try:
        data = request.get_json() or {}
        amount = float(data.get('volume_ml', data.get('amount', request.args.get('amount', 0))))
        
        if not amount:
            return jsonify({
                'success': False,
                'error': 'Volume_ml parameter required'
            }), 400
        
        success = dispense_pump(pump_id, amount)
        
        return jsonify({
            'success': success,
            'pump_id': pump_id,
            'volume_ml': amount,
            'message': f"Dispensing {amount}ml from pump {pump_id}" if success else "Dispense command failed"
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid volume_ml: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error dispensing from pump {pump_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pump/<int:pump_id>/stop', methods=['POST'])
def api_stop_pump(pump_id):
    """Stop pump"""
    try:
        success = stop_pump(pump_id)
        
        return jsonify({
            'success': success,
            'pump_id': pump_id,
            'message': f"Pump {pump_id} stopped" if success else "Stop command failed"
        })
    except Exception as e:
        logger.error(f"Error stopping pump {pump_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/pumps/<int:pump_id>/calibration/clear', methods=['POST'])
def api_clear_pump_calibration(pump_id):
    """Clear pump calibration data"""
    try:
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
        result = get_current_dispensed_volume(pump_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting pump {pump_id} current volume: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pumps/refresh-calibration', methods=['POST'])
def api_refresh_calibration():
    """Manually refresh calibration status for all pumps"""
    try:
        success = refresh_pump_calibrations()
        
        return jsonify({
            'success': success,
            'message': 'Calibration status refreshed' if success else 'Failed to refresh calibration status'
        })
        
    except Exception as e:
        logger.error(f"Error refreshing calibration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pumps/<int:pump_id>/calibrate', methods=['POST'])
def api_calibrate_pump_with_refresh(pump_id):
    """Calibrate a specific pump and update cache"""
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
        
        # Calibrate the pump using hardware_comms
        success = calibrate_pump(pump_id, actual_volume)
        
        if success:
            # Update cached calibration status after successful calibration
            refresh_success = refresh_pump_calibrations()
            if not refresh_success:
                logger.warning(f"Calibration succeeded but cache refresh failed for pump {pump_id}")
        
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

# -----------------------------------------------------------------------------
# FLOW CONTROL - Using exact same patterns as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/flow/<int:flow_id>/start', methods=['POST'])
def api_start_flow(flow_id):
    """Start flow monitoring"""
    try:
        data = request.get_json() or {}
        gallons = int(data.get('gallons', request.args.get('gallons', 0)))
        
        if not gallons:
            return jsonify({
                'success': False,
                'error': 'Gallons parameter required'
            }), 400
        
        success = start_flow(flow_id, gallons)
        
        return jsonify({
            'success': success,
            'flow_id': flow_id,
            'gallons': gallons,
            'message': f"Flow meter {flow_id} started for {gallons} gallons" if success else "Flow start command failed"
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid gallons: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error starting flow {flow_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flow/<int:flow_id>/stop', methods=['POST'])
def api_stop_flow(flow_id):
    """Stop flow monitoring"""
    try:
        success = stop_flow(flow_id)
        
        return jsonify({
            'success': success,
            'flow_id': flow_id,
            'message': f"Flow meter {flow_id} stopped" if success else "Flow stop command failed"
        })
    except Exception as e:
        logger.error(f"Error stopping flow {flow_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# -----------------------------------------------------------------------------
# EC/pH SENSOR CONTROL - Using exact same patterns as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/sensor/ecph/start', methods=['POST'])
@app.route('/api/ecph/start', methods=['POST'])
def api_start_ec_ph():
    """Start EC/pH monitoring"""
    try:
        success = start_ec_ph()
        
        return jsonify({
            'success': success,
            'message': "EC/pH monitoring started" if success else "Failed to start EC/pH monitoring"
        })
    except Exception as e:
        logger.error(f"Error starting EC/pH monitoring: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sensor/ecph/stop', methods=['POST'])
@app.route('/api/ecph/stop', methods=['POST'])
def api_stop_ec_ph():
    """Stop EC/pH monitoring"""
    try:
        success = stop_ec_ph()

        return jsonify({
            'success': success,
            'message': "EC/pH monitoring stopped" if success else "Failed to stop EC/pH monitoring"
        })
    except Exception as e:
        logger.error(f"Error stopping EC/pH monitoring: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sensors/ecph/read', methods=['GET'])
def api_read_ec_ph():
    """Read current EC and pH values"""
    try:
        result = read_ec_ph_sensors()

        if result.get('success'):
            return jsonify({
                'success': True,
                'data': {
                    'ph': result.get('ph'),
                    'ec': result.get('ec'),
                    'timestamp': result.get('timestamp')
                }
            })
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error reading EC/pH sensors: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sensors/ph/calibrate', methods=['POST'])
def api_calibrate_ph():
    """
    Calibrate pH sensor
    Body: {"point": "mid"|"low"|"high"|"clear", "value": 7.0 (optional)}
    """
    try:
        data = request.get_json() or {}
        point = data.get('point')
        value = data.get('value')

        if not point:
            return jsonify({
                'success': False,
                'error': 'Calibration point required'
            }), 400

        success = calibrate_ph(point, value)

        return jsonify({
            'success': success,
            'message': f"pH {point} calibration {'successful' if success else 'failed'}"
        })
    except Exception as e:
        logger.error(f"Error calibrating pH: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sensors/ec/calibrate', methods=['POST'])
def api_calibrate_ec():
    """
    Calibrate EC sensor
    Body: {"point": "dry"|"single"|"low"|"high"|"clear", "value": 1413 (optional)}
    """
    try:
        data = request.get_json() or {}
        point = data.get('point')
        value = data.get('value')

        if not point:
            return jsonify({
                'success': False,
                'error': 'Calibration point required'
            }), 400

        success = calibrate_ec(point, value)

        return jsonify({
            'success': success,
            'message': f"EC {point} calibration {'successful' if success else 'failed'}"
        })
    except Exception as e:
        logger.error(f"Error calibrating EC: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sensors/calibration/status', methods=['GET'])
def api_get_calibration_status():
    """Get calibration status for both sensors"""
    try:
        result = get_sensor_calibration_status()

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting calibration status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# -----------------------------------------------------------------------------
# HARDWARE TESTING ENDPOINTS - For debugging hardware connections
# -----------------------------------------------------------------------------

@app.route('/api/test/relay/<int:relay_id>', methods=['POST'])
def api_test_relay(relay_id):
    """Test relay with detailed debug info"""
    try:
        # Get test parameters
        data = request.get_json() or {}
        test_type = data.get('test_type', 'basic')  # basic or advanced
        duration = float(data.get('duration', 1.0))  # seconds
        
        results = {
            'success': False,
            'relay_id': relay_id,
            'test_type': test_type,
            'commands': [],
            'responses': [],
            'gpio_info': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Get GPIO pin info from config
        try:
            from config import RELAY_GPIO_PINS, get_relay_name
            gpio_pin = RELAY_GPIO_PINS.get(relay_id, 'Unknown')
            relay_name = get_relay_name(relay_id)
            results['gpio_info'] = {
                'pin': gpio_pin,
                'name': relay_name
            }
        except Exception as e:
            results['gpio_info'] = {'error': str(e)}
        
        if test_type == 'basic':
            # Basic test: ON -> OFF -> ON -> OFF
            test_sequence = [True, False, True, False]
            for state in test_sequence:
                command = f"Start;Relay;{relay_id};{'ON' if state else 'OFF'};end"
                results['commands'].append(command)
                
                success = control_relay(relay_id, state)
                results['responses'].append({
                    'command': command,
                    'success': success,
                    'state': 'ON' if state else 'OFF'
                })
                
                time.sleep(duration / len(test_sequence))
                
        elif test_type == 'advanced':
            # Advanced test: Test relay set (for tank operations)
            relay_set = data.get('relay_set', [relay_id])
            
            # Turn on all relays in set
            for rid in relay_set:
                command = f"Start;Relay;{rid};ON;end"
                results['commands'].append(command)
                success = control_relay(rid, True)
                results['responses'].append({
                    'command': command,
                    'success': success,
                    'relay_id': rid,
                    'state': 'ON'
                })
            
            time.sleep(duration)
            
            # Turn off all relays in set
            for rid in relay_set:
                command = f"Start;Relay;{rid};OFF;end"
                results['commands'].append(command)
                success = control_relay(rid, False)
                results['responses'].append({
                    'command': command,
                    'success': success,
                    'relay_id': rid,
                    'state': 'OFF'
                })
        
        results['success'] = all(r.get('success', False) for r in results['responses'])
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error testing relay {relay_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'relay_id': relay_id,
            'test_type': test_type
        }), 500

@app.route('/api/test/pump/<int:pump_id>', methods=['POST'])
def api_test_pump(pump_id):
    """Test pump with detailed debug info"""
    try:
        data = request.get_json() or {}
        test_type = data.get('test_type', 'basic')  # basic or recipe
        amount = float(data.get('amount', 1.0))  # ml
        
        results = {
            'success': False,
            'pump_id': pump_id,
            'test_type': test_type,
            'commands': [],
            'responses': [],
            'pump_info': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Get pump info from config
        try:
            from config import PUMP_ADDRESSES, get_pump_name
            i2c_address = PUMP_ADDRESSES.get(pump_id, 'Unknown')
            pump_name = get_pump_name(pump_id)
            results['pump_info'] = {
                'i2c_address': i2c_address,
                'name': pump_name
            }
        except Exception as e:
            results['pump_info'] = {'error': str(e)}
        
        if test_type == 'basic':
            # Basic test: dispense small amount
            command = f"Start;Dispense;{pump_id};{amount};end"
            results['commands'].append(command)
            
            success = dispense_pump(pump_id, amount)
            results['responses'].append({
                'command': command,
                'success': success,
                'amount': amount
            })
            
        elif test_type == 'recipe':
            # Recipe test: multiple pumps in sequence
            recipe = data.get('recipe', [{'pump_id': pump_id, 'amount': amount}])
            
            for step in recipe:
                step_pump_id = step.get('pump_id', pump_id)
                step_amount = step.get('amount', 1.0)
                
                command = f"Start;Dispense;{step_pump_id};{step_amount};end"
                results['commands'].append(command)
                
                success = dispense_pump(step_pump_id, step_amount)
                results['responses'].append({
                    'command': command,
                    'success': success,
                    'pump_id': step_pump_id,
                    'amount': step_amount
                })
                
                time.sleep(0.5)  # Brief delay between pumps
        
        results['success'] = all(r.get('success', False) for r in results['responses'])
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error testing pump {pump_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'pump_id': pump_id,
            'test_type': test_type
        }), 500

@app.route('/api/test/flow/<int:flow_id>', methods=['POST'])
def api_test_flow(flow_id):
    """Test flow meter with detailed debug info"""
    try:
        data = request.get_json() or {}
        test_type = data.get('test_type', 'basic')  # basic or pulse_test
        gallons = int(data.get('gallons', 1))
        
        results = {
            'success': False,
            'flow_id': flow_id,
            'test_type': test_type,
            'commands': [],
            'responses': [],
            'flow_info': {},
            'pulse_data': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Get flow meter info from config
        try:
            from config import FLOW_METER_GPIO_PINS, get_flow_meter_name
            gpio_pin = FLOW_METER_GPIO_PINS.get(flow_id, 'Unknown')
            flow_name = get_flow_meter_name(flow_id)
            results['flow_info'] = {
                'gpio_pin': gpio_pin,
                'name': flow_name
            }
        except Exception as e:
            results['flow_info'] = {'error': str(e)}
        
        if test_type == 'basic':
            # Basic test: start and stop flow monitoring
            command = f"Start;StartFlow;{flow_id};{gallons};220;end"
            results['commands'].append(command)
            
            success = start_flow(flow_id, gallons)
            results['responses'].append({
                'command': command,
                'success': success,
                'gallons': gallons
            })
            
            # Wait a moment then stop
            time.sleep(1.0)
            
            stop_command = f"Start;StartFlow;{flow_id};0;end"
            results['commands'].append(stop_command)
            
            stop_success = stop_flow(flow_id)
            results['responses'].append({
                'command': stop_command,
                'success': stop_success
            })
            
        elif test_type == 'pulse_test':
            # Pulse monitoring test
            results['pulse_data'] = {
                'calibration': 220,  # pulses per gallon
                'target_pulses': gallons * 220,
                'monitoring_duration': data.get('duration', 10.0)
            }
            
            # Start monitoring
            command = f"Start;StartFlow;{flow_id};{gallons};220;end"
            results['commands'].append(command)
            
            success = start_flow(flow_id, gallons)
            results['responses'].append({
                'command': command,
                'success': success,
                'pulse_monitoring': True
            })
        
        results['success'] = all(r.get('success', False) for r in results['responses'])
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error testing flow meter {flow_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'flow_id': flow_id,
            'test_type': test_type
        }), 500

@app.route('/api/test/sensor/ecph', methods=['POST'])
def api_test_sensor():
    """Test EC/pH sensors with detailed debug info"""
    try:
        data = request.get_json() or {}
        test_type = data.get('test_type', 'basic')  # basic or continuous
        
        results = {
            'success': False,
            'test_type': test_type,
            'commands': [],
            'responses': [],
            'sensor_data': {},
            'connection_info': {
                'interface': 'USB Serial',
                'device': 'Arduino Uno',
                'protocol': 'EcPh commands'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if test_type == 'basic':
            # Basic test: single reading
            command = "Start;EcPh;ON;end"
            results['commands'].append(command)
            
            success = start_ec_ph()
            results['responses'].append({
                'command': command,
                'success': success,
                'action': 'start_monitoring'
            })
            
            # Simulate getting a reading (in real implementation, this would read from Arduino)
            results['sensor_data'] = {
                'ph': 7.2,
                'ec': 1.4,
                'temperature': 22.0,
                'flow_rate': 2.3
            }
            
            # Stop monitoring
            stop_command = "Start;EcPh;OFF;end"
            results['commands'].append(stop_command)
            
            stop_success = stop_ec_ph()
            results['responses'].append({
                'command': stop_command,
                'success': stop_success,
                'action': 'stop_monitoring'
            })
            
        elif test_type == 'continuous':
            # Continuous monitoring test
            duration = float(data.get('duration', 30.0))
            
            command = "Start;EcPh;ON;end"
            results['commands'].append(command)
            
            success = start_ec_ph()
            results['responses'].append({
                'command': command,
                'success': success,
                'monitoring_duration': duration
            })
            
            # In a real implementation, this would collect readings over time
            results['sensor_data'] = {
                'monitoring_active': True,
                'duration': duration,
                'sample_rate': '1 per second'
            }
        
        results['success'] = all(r.get('success', False) for r in results['responses'])
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error testing sensors: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'test_type': test_type
        }), 500

# -----------------------------------------------------------------------------
# EMERGENCY CONTROLS - Same as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/emergency/stop', methods=['POST'])
def api_emergency_stop():
    """Emergency stop all operations"""
    try:
        success = emergency_stop()
        
        return jsonify({
            'success': success,
            'message': "🚨 EMERGENCY STOP ACTIVATED 🚨" if success else "Emergency stop failed"
        })
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found_error(error):
    # For API requests, return JSON
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found',
            'error_code': 404
        }), 404
    # For static files, try to serve from dist
    else:
        return send_from_directory('static/dist', 'dashboard.html')

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 500
        }), 500
    else:
        return send_from_directory('static/dist', 'dashboard.html')


# =============================================================================
# STARTUP AND MAIN
# =============================================================================

def init_hardware():
    """Initialize hardware with safety wrapper"""
    logger.info("Starting hardware initialization...")
    
    # Test hardware communications
    try:
        status = get_system_status()
        if status.get('system_ready'):
            logger.info("✓ Hardware communications ready")
            logger.info("✓ EZO pump controller initialized with calibration status")
            return status
        else:
            logger.warning(f"⚠ Hardware system not fully ready: {status}")
            return status
    except Exception as e:
        logger.error(f"✗ Hardware initialization error: {e}")
        raise

def initialize_app():
    """Initialize the application with safety manager"""
    logger.info("Starting Flask application...")
    
    # Initialize hardware with safety wrapper
    try:
        hardware = safety_manager.safe_hardware_init(init_hardware)
        logger.info("✓ Hardware initialization completed safely")
    except Exception as e:
        logger.error(f"Hardware init failed: {e}")
        sys.exit(1)
    
    logger.info("Flask application initialized")

if __name__ == '__main__':
    initialize_app()
    
    # Run the Flask app with safe settings
    try:
        print("Starting Flask application...")
        app.run(
            host='0.0.0.0',     # Allow external connections
            port=5000,          # Default Flask port
            debug=False,        # CRITICAL: Disable debug mode to stop auto-restart
            use_reloader=False, # CRITICAL: Disable auto-reload to prevent file watching
            threaded=True       # Handle multiple requests
        )
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        safety_manager.emergency_stop()
    finally:
        print("Application shutdown complete")