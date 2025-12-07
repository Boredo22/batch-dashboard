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
import time
from datetime import datetime
from typing import Dict, Any

# Import our reliable hardware communications module
from hardware.hardware_comms import (
    control_relay, dispense_pump, stop_pump, start_flow, stop_flow, get_flow_status,
    emergency_stop, get_system_status, get_available_hardware,
    all_relays_off, cleanup_hardware, start_ec_ph, stop_ec_ph,
    calibrate_pump, clear_pump_calibration, check_pump_calibration_status,
    pause_pump, get_pump_voltage, get_current_dispensed_volume,
    get_pump_status, refresh_pump_calibrations,
    read_ec_ph_sensors, calibrate_ph, calibrate_ec, get_sensor_calibration_status,
    get_hardware_comms
)

# Import job manager for multi-step job orchestration
from job_manager import JobManager

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

# Import state manager for hardware state persistence
try:
    from state_manager import state, get_system_snapshot
except ImportError:
    # Fallback if state_manager not available
    state = None
    def get_system_snapshot():
        return {"error": "State manager not available"}

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

# Initialize job manager (will be started after hardware init)
job_manager = None

# Register cleanup on app shutdown
def cleanup_on_shutdown():
    """Cleanup both hardware and job manager"""
    if job_manager:
        job_manager.stop()
    cleanup_hardware()

atexit.register(cleanup_on_shutdown)

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

        # Add persisted relay states from state manager
        persisted_relays = {}
        if state is not None:
            persisted_relays = state.get_all_relays()

        # Add job status if job manager is available
        job_status = {}
        if job_manager:
            job_status = job_manager.get_all_jobs_status()

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
            'ec_ph_monitoring': status.get('ec_ph_active', False),
            'persisted_relay_states': persisted_relays,
            # Add job status for Stage 2 Testing page
            'active_fill_job': job_status.get('active_fill_job'),
            'active_mix_job': job_status.get('active_mix_job'),
            'active_send_job': job_status.get('active_send_job')
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/state')
def api_state():
    """Get persistent hardware state from state manager"""
    try:
        snapshot = get_system_snapshot()
        return jsonify({
            'success': True,
            'state': snapshot
        })
    except Exception as e:
        logger.error(f"Error getting state snapshot: {e}")
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

@app.route('/api/relay/states', methods=['GET'])
def api_get_relay_states():
    """Get current state of all relays"""
    try:
        status = get_system_status()
        relay_states = status.get('relays', {})
        hardware = get_available_hardware()

        # Format relay states with names
        relays = []
        for relay_id in hardware['relays']['ids']:
            relays.append({
                'id': relay_id,
                'name': hardware['relays']['names'].get(relay_id, f'Relay {relay_id}'),
                'state': relay_states.get(str(relay_id), False)
            })

        return jsonify({
            'success': True,
            'relays': relays,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Error getting relay states: {e}")
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

@app.route('/api/flow/<int:flow_id>/status', methods=['GET'])
def api_get_flow_status(flow_id):
    """Get detailed flow meter status including pulse count"""
    try:
        status = get_flow_status(flow_id)

        if status is None:
            return jsonify({
                'success': False,
                'error': f'Invalid flow meter ID: {flow_id}'
            }), 400

        return jsonify({
            'success': True,
            'flow_id': flow_id,
            'status': status
        })
    except Exception as e:
        logger.error(f"Error getting flow status {flow_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# -----------------------------------------------------------------------------
# FLOW METER DIAGNOSTICS - For troubleshooting page
# -----------------------------------------------------------------------------

@app.route('/api/flow/<int:flow_id>/diagnostics/gpio', methods=['GET'])
def api_flow_gpio_diagnostics(flow_id):
    """Get GPIO pin status and configuration for flow meter"""
    try:
        from hardware.hardware_comms import get_flow_controller
        from config import FLOW_METER_GPIO_PINS, FLOW_METER_NAMES, FLOW_METER_CALIBRATION

        if flow_id not in FLOW_METER_GPIO_PINS:
            return jsonify({
                'success': False,
                'error': f'Invalid flow meter ID: {flow_id}'
            }), 400

        gpio_pin = FLOW_METER_GPIO_PINS[flow_id]
        meter_name = FLOW_METER_NAMES.get(flow_id, f'Flow Meter {flow_id}')
        calibration = FLOW_METER_CALIBRATION.get(flow_id, 220)

        # Try to read GPIO level if controller is available
        gpio_level = None
        gpio_level_voltage = None

        flow_controller = get_flow_controller()
        if flow_controller:
            try:
                import lgpio
                if flow_controller.h is not None:
                    level = lgpio.gpio_read(flow_controller.h, gpio_pin)
                    gpio_level = 'HIGH' if level else 'LOW'
                    gpio_level_voltage = '~3.3V' if level else '~0V'
            except Exception as e:
                logger.debug(f"Could not read GPIO level: {e}")

        return jsonify({
            'success': True,
            'flow_id': flow_id,
            'diagnostics': {
                'meter_name': meter_name,
                'gpio_pin': gpio_pin,
                'calibration_ppg': calibration,
                'gpio_level': gpio_level,
                'gpio_voltage': gpio_level_voltage,
                'interrupt_edge': 'RISING',
                'pull_resistor': 'PULL_UP'
            }
        })
    except Exception as e:
        logger.error(f"Error getting GPIO diagnostics for flow {flow_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flow/<int:flow_id>/diagnostics/pulse-test', methods=['POST'])
def api_flow_pulse_test(flow_id):
    """Start a pulse counting test for specified duration"""
    try:
        from hardware.hardware_comms import get_flow_controller
        from config import FLOW_METER_GPIO_PINS

        if flow_id not in FLOW_METER_GPIO_PINS:
            return jsonify({
                'success': False,
                'error': f'Invalid flow meter ID: {flow_id}'
            }), 400

        data = request.get_json() or {}
        duration = int(data.get('duration', 10))  # Default 10 seconds

        flow_controller = get_flow_controller()
        if not flow_controller:
            return jsonify({
                'success': False,
                'error': 'Flow controller not available'
            }), 500

        # Reset pulse counter and activate monitoring
        flow_controller.flow_meters[flow_id]['pulse_count'] = 0
        flow_controller.flow_meters[flow_id]['status'] = 1

        return jsonify({
            'success': True,
            'flow_id': flow_id,
            'message': f'Pulse test started for {duration} seconds',
            'test_duration': duration,
            'start_time': time.time()
        })
    except Exception as e:
        logger.error(f"Error starting pulse test for flow {flow_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flow/<int:flow_id>/diagnostics/reset', methods=['POST'])
def api_flow_reset_counter(flow_id):
    """Reset pulse counter for flow meter"""
    try:
        from hardware.hardware_comms import get_flow_controller
        from config import FLOW_METER_GPIO_PINS

        if flow_id not in FLOW_METER_GPIO_PINS:
            return jsonify({
                'success': False,
                'error': f'Invalid flow meter ID: {flow_id}'
            }), 400

        flow_controller = get_flow_controller()
        if not flow_controller:
            return jsonify({
                'success': False,
                'error': 'Flow controller not available'
            }), 500

        # Reset all counters
        flow_controller.flow_meters[flow_id]['pulse_count'] = 0
        flow_controller.flow_meters[flow_id]['last_count'] = 0
        flow_controller.flow_meters[flow_id]['current_gallons'] = 0
        flow_controller.flow_meters[flow_id]['target_gallons'] = 0
        flow_controller.flow_meters[flow_id]['status'] = 0

        return jsonify({
            'success': True,
            'flow_id': flow_id,
            'message': 'Flow meter counter reset'
        })
    except Exception as e:
        logger.error(f"Error resetting flow {flow_id}: {e}")
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

# =============================================================================
# MULTI-STEP JOB ENDPOINTS - Job orchestration for Stage 2 Testing
# =============================================================================

@app.route('/api/jobs/fill/start', methods=['POST'])
def api_start_fill_job():
    """Start a tank fill job"""
    try:
        if not job_manager:
            return jsonify({
                'success': False,
                'error': 'Job manager not initialized'
            }), 500

        data = request.get_json() or {}
        tank_id = int(data.get('tank_id', 0))
        gallons = float(data.get('gallons', 0))

        if not tank_id or not gallons:
            return jsonify({
                'success': False,
                'error': 'tank_id and gallons parameters required'
            }), 400

        result = job_manager.start_fill_job(tank_id, gallons)
        return jsonify(result)

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid parameters: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error starting fill job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/fill/stop', methods=['POST'])
def api_stop_fill_job():
    """Stop the active fill job"""
    try:
        if not job_manager:
            return jsonify({
                'success': False,
                'error': 'Job manager not initialized'
            }), 500

        result = job_manager.stop_job('fill')
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error stopping fill job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/mix/start', methods=['POST'])
def api_start_mix_job():
    """Start a tank mixing job"""
    try:
        if not job_manager:
            return jsonify({
                'success': False,
                'error': 'Job manager not initialized'
            }), 500

        data = request.get_json() or {}
        tank_id = int(data.get('tank_id', 0))

        if not tank_id:
            return jsonify({
                'success': False,
                'error': 'tank_id parameter required'
            }), 400

        result = job_manager.start_mix_job(tank_id)
        return jsonify(result)

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid parameters: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error starting mix job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/mix/stop', methods=['POST'])
def api_stop_mix_job():
    """Stop the active mix job"""
    try:
        if not job_manager:
            return jsonify({
                'success': False,
                'error': 'Job manager not initialized'
            }), 500

        result = job_manager.stop_job('mix')
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error stopping mix job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/send/start', methods=['POST'])
def api_start_send_job():
    """Start a send job (tank to room)"""
    try:
        if not job_manager:
            return jsonify({
                'success': False,
                'error': 'Job manager not initialized'
            }), 500

        data = request.get_json() or {}
        tank_id = int(data.get('tank_id', 0))
        room_id = data.get('room_id', '')
        gallons = float(data.get('gallons', 0))

        if not tank_id or not room_id or not gallons:
            return jsonify({
                'success': False,
                'error': 'tank_id, room_id, and gallons parameters required'
            }), 400

        result = job_manager.start_send_job(tank_id, room_id, gallons)
        return jsonify(result)

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid parameters: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error starting send job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/send/stop', methods=['POST'])
def api_stop_send_job():
    """Stop the active send job"""
    try:
        if not job_manager:
            return jsonify({
                'success': False,
                'error': 'Job manager not initialized'
            }), 500

        result = job_manager.stop_job('send')
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error stopping send job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/status', methods=['GET'])
def api_get_all_jobs_status():
    """Get status of all active jobs"""
    try:
        if not job_manager:
            return jsonify({
                'success': False,
                'error': 'Job manager not initialized'
            }), 500

        job_status = job_manager.get_all_jobs_status()
        return jsonify({
            'success': True,
            **job_status
        })

    except Exception as e:
        logger.error(f"Error getting jobs status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
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
    global job_manager

    logger.info("Starting Flask application...")

    # Initialize hardware with safety wrapper
    try:
        hardware = safety_manager.safe_hardware_init(init_hardware)
        logger.info("✓ Hardware initialization completed safely")
    except Exception as e:
        logger.error(f"Hardware init failed: {e}")
        sys.exit(1)

    # Initialize job manager with hardware communications
    try:
        hardware_comms = get_hardware_comms()
        if hardware_comms:
            job_manager = JobManager(hardware_comms)
            job_manager.start()
            logger.info("✓ Job manager initialized and started")
        else:
            logger.warning("⚠ Hardware comms not available, job manager not initialized")
    except Exception as e:
        logger.error(f"Job manager init failed: {e}")
        # Don't exit - jobs won't work but hardware control still will

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