#!/usr/bin/env python3
"""
Flask API Server for Nutrient Mixing System
Provides REST API endpoints for Svelte frontend
Uses hardware_comms.py for reliable hardware control like simple_gui.py
"""

# CRITICAL: Import hardware safety FIRST
from hardware_safety import setup_hardware_safety
import sys
import time

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import logging
import atexit
from datetime import datetime
from typing import Dict, Any
import json
import threading

# Import our reliable hardware communications module
from hardware.hardware_comms import (
    control_relay, dispense_pump, stop_pump, start_flow, stop_flow,
    emergency_stop, get_system_status, get_available_hardware,
    all_relays_off, cleanup_hardware, start_ec_ph, stop_ec_ph,
    calibrate_pump, clear_pump_calibration, check_pump_calibration_status,
    pause_pump, get_pump_voltage, get_current_dispensed_volume,
    get_pump_status, refresh_pump_calibrations,
    read_ec_ph_sensors, calibrate_ph, calibrate_ec, get_sensor_calibration_status,
    get_flow_status, get_tank_monitor_readings
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


def api_endpoint(func):
    """Wrap a route handler with the standard JSON error envelope.

    Replaces the per-handler `try / except Exception -> logger.error +
    jsonify(success=False, error=...), 500` boilerplate that was repeated in
    ~40 handlers. Handlers can still early-return their own responses
    (validation 400s, custom statuses, etc.); only an *uncaught* exception is
    turned into a 500 here.
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return wrapper


# =============================================================================
# SETTINGS JSON PERSISTENCE
# =============================================================================

import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

def _build_default_settings():
    """Build default settings from config.py values"""
    return {
        'user': {
            'tanks': getattr(config, 'TANKS', {}),
            'rooms': getattr(config, 'ROOMS', {}),
            'pumps': {
                'names': getattr(config, 'PUMP_NAMES', {}),
                'addresses': getattr(config, 'PUMP_ADDRESSES', {})
            },
            'flowMeters': {
                'calibration': getattr(config, 'FLOW_METER_CALIBRATION', {})
            },
            'ecphDefaults': {
                'ec': {'min': 1.0, 'max': 2.0},
                'ph': {'min': 5.5, 'max': 6.5}
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
            },
            'growDefaults': {
                'veg_days': 28,
                'flower_days': 50,
                'flush_days': 14,
                'flower_veg_nute_days': 21,
                'feedings_per_day': 2,
                'default_watering_volume': 50
            }
        },
        'developer': {
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
    }


def load_settings():
    """Load settings from JSON file, creating with defaults if missing"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading {SETTINGS_FILE}, regenerating defaults: {e}")

    # File missing or corrupt — write defaults
    defaults = _build_default_settings()
    save_settings(defaults)
    return defaults


def save_settings(data):
    """Write settings dict to JSON file"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


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
@api_endpoint
def api_get_config():
    """Get current system configuration"""
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
    

@app.route('/api/config', methods=['POST'])
@api_endpoint
def api_save_config():
    """Save system configuration changes"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'No configuration data provided'
        }), 400
    
    # This legacy endpoint never persisted anything - it only logged. Rather
    # than return a misleading "saved successfully", report honestly and
    # point callers at the endpoints that actually persist settings.
    logger.warning(
        "Deprecated /api/config POST called; this endpoint does not persist. "
        "Use POST /api/settings/user and /api/settings/developer instead."
    )
    return jsonify({
        'success': False,
        'error': 'Not implemented: use /api/settings/user and '
                 '/api/settings/developer to persist settings.'
    }), 501


@app.route('/api/config/pumps', methods=['GET'])
@api_endpoint
def api_get_pump_config():
    """Get pump id -> name mapping for the growers dashboard."""
    return jsonify({
        'pump_names': getattr(config, 'PUMP_NAMES', {})
    })


# =============================================================================
# SETTINGS ENDPOINTS - User and Developer Settings
# =============================================================================

@app.route('/api/settings/user', methods=['GET'])
@api_endpoint
def api_get_user_settings():
    """Get user settings from settings.json"""
    settings = load_settings()
    return jsonify(settings.get('user', {}))

@app.route('/api/settings/user', methods=['POST'])
@api_endpoint
def api_save_user_settings():
    """Save user settings to settings.json"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No user settings data provided'}), 400

    settings = load_settings()
    settings['user'] = data
    save_settings(settings)

    logger.info("User settings saved to settings.json")
    return jsonify({
        'success': True,
        'message': 'User settings saved successfully',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/settings/developer', methods=['GET'])
@api_endpoint
def api_get_developer_settings():
    """Get developer settings from settings.json"""
    settings = load_settings()
    return jsonify(settings.get('developer', {}))

@app.route('/api/settings/developer', methods=['POST'])
@api_endpoint
def api_save_developer_settings():
    """Save developer settings to settings.json"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No developer settings data provided'}), 400

    settings = load_settings()
    settings['developer'] = data
    save_settings(settings)

    logger.info("Developer settings saved to settings.json")
    return jsonify({
        'success': True,
        'message': 'Developer settings saved successfully',
        'timestamp': datetime.now().isoformat()
    })

# =============================================================================
# NUTRIENTS CONFIGURATION ENDPOINTS - Separate nutrients management
# =============================================================================

@app.route('/api/nutrients', methods=['GET'])
@api_endpoint
def api_get_nutrients():
    """Get nutrients configuration"""
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
                "PK Synergy": 7,
                "Runclean": 6,
                "pH Down": 8
            }
        }
        # Save default configuration
        with open(nutrients_file, 'w') as f:
            json.dump(nutrients_data, f, indent=2)
    
    return jsonify(nutrients_data)
    

@app.route('/api/nutrients', methods=['POST'])
@api_endpoint
def api_save_nutrients():
    """Save nutrients configuration"""
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
    

# =============================================================================
# GROW CYCLES ENDPOINTS - Plant cycle tracking and daily reports
# =============================================================================

GROW_CYCLES_FILE = 'grow_cycles.json'

@app.route('/api/grow-cycles', methods=['GET'])
@api_endpoint
def api_get_grow_cycles():
    """Get grow cycles configuration"""
    import json
    import os

    if os.path.exists(GROW_CYCLES_FILE):
        with open(GROW_CYCLES_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {"cycles": {}}
        with open(GROW_CYCLES_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    return jsonify(data)


@app.route('/api/grow-cycles', methods=['POST'])
@api_endpoint
def api_save_grow_cycles():
    """Save grow cycles configuration"""
    import json

    data = request.get_json()
    if not data or 'cycles' not in data:
        return jsonify({'success': False, 'error': 'Missing cycles data'}), 400

    # Validate each cycle
    required_fields = ['room_id', 'start_date', 'veg_days', 'flower_days', 'flush_days']
    for room_id, cycle in data['cycles'].items():
        for field in required_fields:
            if field not in cycle:
                return jsonify({
                    'success': False,
                    'error': f'Cycle for room {room_id} missing required field: {field}'
                }), 400
        # Validate date format
        try:
            from datetime import date as dt_date
            dt_date.fromisoformat(cycle['start_date'])
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid date format for room {room_id}: {cycle["start_date"]}'
            }), 400
        # Validate day counts are positive
        for day_field in ['veg_days', 'flower_days', 'flush_days']:
            if not isinstance(cycle[day_field], (int, float)) or cycle[day_field] < 0:
                return jsonify({
                    'success': False,
                    'error': f'Invalid {day_field} for room {room_id}: must be a non-negative number'
                }), 400

    with open(GROW_CYCLES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info("Grow cycles saved successfully")
    return jsonify({
        'success': True,
        'message': 'Grow cycles saved successfully',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/grow-cycles/report', methods=['GET'])
@api_endpoint
def api_get_grow_cycles_report():
    """Compute daily watering reports for all active cycles"""
    from grow_cycles import build_reports

    # Load cycles
    if not os.path.exists(GROW_CYCLES_FILE):
        return jsonify({'reports': []})
    with open(GROW_CYCLES_FILE, 'r') as f:
        cycles_data = json.load(f)

    # Load nutrients
    nutrients_data = {}
    if os.path.exists('nutrients.json'):
        with open('nutrients.json', 'r') as f:
            nutrients_data = json.load(f)

    # Load grow defaults from settings
    settings_data = load_settings()
    grow_defaults = settings_data.get('user', {}).get('growDefaults', {})

    # All the agronomic math now lives in the pure, testable grow_cycles module.
    reports = build_reports(cycles_data, nutrients_data, grow_defaults)
    return jsonify({'reports': reports})


# =============================================================================
# API ENDPOINTS - Hardware Control (same patterns as simple_gui.py)
# =============================================================================

def _batch_job_snapshot():
    """Live batch dosing job status for the status payload (None if no job)."""
    try:
        import dosing_job
        job = dosing_job.get_current()
        return job.snapshot() if job else None
    except Exception as e:
        logger.debug(f"batch job snapshot unavailable: {e}")
        return None


def build_status_data():
    """Build the status data structure (shared between REST and SSE endpoints)"""
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

    # Surface LIVE flow-meter status from the controller instead of hardcoding
    # stopped/0. main.get_system_status() already returns real per-meter data
    # (keyed by meter id) via flow_controller.get_all_flow_status(); previously
    # that was discarded here, which made every consumer see a meter that never
    # ran. The fill workflow's "wait for flow to complete" therefore resolved
    # instantly (status was never 'running'), so tanks never reached target.
    # The controller's integer status (0=inactive, 1=active, 2=completed) is
    # mapped to the string the frontend checks ('running' vs anything else), and
    # both total_gallons and current_gallons are emitted so every flow card works.
    raw_flow = status.get('flow_meters') or {}
    flow_status_str = {0: 'stopped', 1: 'running', 2: 'completed'}
    flow_meters_list = []
    for fid in hardware['flow_meters']['ids']:
        fm = raw_flow.get(fid) or raw_flow.get(str(fid)) or {}
        gallons = fm.get('current_gallons', 0)
        flow_meters_list.append({
            'id': fid,
            'name': hardware['flow_meters']['names'].get(fid, f'Flow Meter {fid}'),
            'status': flow_status_str.get(fm.get('status', 0), 'stopped'),
            'flow_rate': fm.get('flow_rate', 0),
            'total_gallons': gallons,
            'current_gallons': gallons,
            'target_gallons': fm.get('target_gallons', 0),
            'pulse_count': fm.get('pulse_count', 0),
        })

    return {
        'success': True,
        'status': status,
        'hardware': hardware,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        # Add data in the format expected by Dashboard.svelte
        'relays': [{'id': rid, 'name': hardware['relays']['names'].get(rid, f'Relay {rid}'), 'state': status['relays'].get(str(rid), False)}
                  for rid in hardware['relays']['ids']],
        'pumps': pumps_list,
        'flow_meters': flow_meters_list,
        'ec_value': status.get('ec', 0),
        'ph_value': status.get('ph', 0),
        'ec_ph_monitoring': status.get('ec_ph_active', False),
        'tank_monitors': status.get('tank_monitors', {}),
        'batch_job': _batch_job_snapshot()
    }


@app.route('/api/system/status')
@api_endpoint
def api_status():
    """Get current system status"""
    return jsonify(build_status_data())


@app.route('/api/hardware/pumps', methods=['GET'])
@api_endpoint
def api_hardware_pumps():
    """List pumps with their configured names (growers dashboard fallback)."""
    pump_names = getattr(config, 'PUMP_NAMES', {})
    return jsonify({
        'pumps': [{'id': pump_id, 'name': name} for pump_id, name in pump_names.items()]
    })


# =============================================================================
# SERVER-SENT EVENTS (SSE) - Real-time status streaming
# =============================================================================

@app.route('/api/system/status/stream')
def api_status_stream():
    """
    SSE endpoint for real-time system status updates.
    Pushes status updates every 2 seconds to connected clients.
    """
    def generate():
        """Generator function that yields SSE events"""
        while True:
            try:
                # Build status data
                data = build_status_data()

                # Format as SSE event
                # SSE format: "data: <json>\n\n"
                yield f"data: {json.dumps(data)}\n\n"

                # Wait before sending next update (2 seconds matches current polling interval)
                import time as time_module
                time_module.sleep(2)

            except GeneratorExit:
                # Client disconnected
                logger.info("SSE client disconnected")
                break
            except Exception as e:
                # Send error event and continue
                logger.error(f"SSE error: {e}")
                error_data = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                import time as time_module
                time_module.sleep(5)  # Wait longer on error before retry

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering if present
            'Access-Control-Allow-Origin': '*'  # Allow CORS for SSE
        }
    )

# -----------------------------------------------------------------------------
# RELAY CONTROL - Using exact same patterns as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/relay/<int:relay_id>/<state>', methods=['GET', 'POST'])
def api_control_relay(relay_id, state):
    """Control individual relay"""
    import time as _time
    start_time = _time.time()
    logger.info(f"[RELAY API] Request received: relay={relay_id}, state={state}")

    try:
        # Convert state string to boolean
        relay_state = state.lower() in ['on', 'true', '1']

        logger.info(f"[RELAY API] Calling control_relay...")
        success = control_relay(relay_id, relay_state)
        elapsed = _time.time() - start_time
        logger.info(f"[RELAY API] control_relay returned in {elapsed:.3f}s, success={success}")

        return jsonify({
            'success': success,
            'relay_id': relay_id,
            'state': 'ON' if relay_state else 'OFF',
            'message': f"Relay {relay_id} {'turned on' if relay_state else 'turned off'}" if success else "Command failed"
        })
    except Exception as e:
        elapsed = _time.time() - start_time
        logger.error(f"[RELAY API] Error after {elapsed:.3f}s controlling relay {relay_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/relay/all/off', methods=['POST'])
@api_endpoint
def api_all_relays_off():
    """Turn all relays off"""
    success = all_relays_off()
    
    return jsonify({
        'success': success,
        'message': "All relays turned off" if success else "Failed to turn off relays"
    })

# -----------------------------------------------------------------------------
# PUMP CONTROL - Using exact same patterns as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/pump/<int:pump_id>/dispense', methods=['POST'])
@api_endpoint
def api_dispense_pump(pump_id):
    """Start pump dispensing"""
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

@app.route('/api/pumps/<int:pump_id>/dispense', methods=['POST'])
@api_endpoint
def api_dispense_pump_plural(pump_id):
    """Start pump dispensing (plural endpoint for HeadGrower)"""
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

@app.route('/api/pump/<int:pump_id>/stop', methods=['POST'])
@app.route('/api/pumps/<int:pump_id>/stop', methods=['POST'])
@api_endpoint
def api_stop_pump(pump_id):
    """Stop pump"""
    success = stop_pump(pump_id)
    
    return jsonify({
        'success': success,
        'pump_id': pump_id,
        'message': f"Pump {pump_id} stopped" if success else "Stop command failed"
    })


@app.route('/api/pumps/<int:pump_id>/calibration/clear', methods=['POST'])
@api_endpoint
def api_clear_pump_calibration(pump_id):
    """Clear pump calibration data"""
    success = clear_pump_calibration(pump_id)
    
    return jsonify({
        'success': success,
        'pump_id': pump_id,
        'message': f"Pump {pump_id} calibration cleared" if success else "Failed to clear calibration"
    })
    

@app.route('/api/pumps/<int:pump_id>/calibration/status', methods=['GET'])
@api_endpoint
def api_check_pump_calibration_status(pump_id):
    """Check pump calibration status"""
    result = check_pump_calibration_status(pump_id)
    
    return jsonify(result)
    

@app.route('/api/pumps/<int:pump_id>/pause', methods=['POST'])
@api_endpoint
def api_pause_pump(pump_id):
    """Pause pump during dispensing"""
    success = pause_pump(pump_id)
    
    return jsonify({
        'success': success,
        'pump_id': pump_id,
        'message': f"Pump {pump_id} paused" if success else "Failed to pause pump"
    })
    

@app.route('/api/pumps/<int:pump_id>/status', methods=['GET'])
@api_endpoint
def api_get_pump_status(pump_id):
    """Get comprehensive pump status including voltage, calibration, and current volume"""
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
    

@app.route('/api/pumps/<int:pump_id>/volume', methods=['GET'])
@api_endpoint
def api_get_current_volume(pump_id):
    """Get current dispensed volume from pump"""
    result = get_current_dispensed_volume(pump_id)
    
    return jsonify(result)
    

@app.route('/api/pumps/refresh-calibration', methods=['POST'])
@api_endpoint
def api_refresh_calibration():
    """Manually refresh calibration status for all pumps"""
    success = refresh_pump_calibrations()
    
    return jsonify({
        'success': success,
        'message': 'Calibration status refreshed' if success else 'Failed to refresh calibration status'
    })
    

@app.route('/api/pumps/<int:pump_id>/calibrate', methods=['POST'])
@api_endpoint
def api_calibrate_pump_with_refresh(pump_id):
    """Calibrate a specific pump and update cache"""
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
    

# -----------------------------------------------------------------------------
# FLOW CONTROL - Using exact same patterns as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/flow/<int:flow_id>/start', methods=['POST'])
@api_endpoint
def api_start_flow(flow_id):
    """Start flow monitoring"""
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

@app.route('/api/flow/<int:flow_id>/stop', methods=['POST'])
@api_endpoint
def api_stop_flow(flow_id):
    """Stop flow monitoring"""
    success = stop_flow(flow_id)
    
    return jsonify({
        'success': success,
        'flow_id': flow_id,
        'message': f"Flow meter {flow_id} stopped" if success else "Flow stop command failed"
    })

@app.route('/api/flow/<int:flow_id>/status', methods=['GET'])
@api_endpoint
def api_get_flow_status(flow_id):
    """Get detailed flow meter status including pulse count"""
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

# -----------------------------------------------------------------------------
# FLOW METER DIAGNOSTICS - For troubleshooting page
# -----------------------------------------------------------------------------

@app.route('/api/flow/<int:flow_id>/diagnostics/gpio', methods=['GET'])
@api_endpoint
def api_flow_gpio_diagnostics(flow_id):
    """Get GPIO pin status and configuration for flow meter"""
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

@app.route('/api/flow/<int:flow_id>/diagnostics/pulse-test', methods=['POST'])
@api_endpoint
def api_flow_pulse_test(flow_id):
    """Start a pulse counting test for specified duration"""
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

@app.route('/api/flow/<int:flow_id>/diagnostics/reset', methods=['POST'])
@api_endpoint
def api_flow_reset_counter(flow_id):
    """Reset pulse counter for flow meter"""
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

# -----------------------------------------------------------------------------
# EC/pH SENSOR CONTROL - Using exact same patterns as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/ecph/start', methods=['POST'])
@api_endpoint
def api_start_ec_ph():
    """Start EC/pH monitoring"""
    success = start_ec_ph()
    
    return jsonify({
        'success': success,
        'message': "EC/pH monitoring started" if success else "Failed to start EC/pH monitoring"
    })

@app.route('/api/ecph/stop', methods=['POST'])
@api_endpoint
def api_stop_ec_ph():
    """Stop EC/pH monitoring"""
    success = stop_ec_ph()

    return jsonify({
        'success': success,
        'message': "EC/pH monitoring stopped" if success else "Failed to stop EC/pH monitoring"
    })

@app.route('/api/sensors/ecph/read', methods=['GET'])
@api_endpoint
def api_read_ec_ph():
    """Read current EC and pH values"""
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

@app.route('/api/sensors/ph/calibrate', methods=['POST'])
@api_endpoint
def api_calibrate_ph():
    """
    Calibrate pH sensor
    Body: {"point": "mid"|"low"|"high"|"clear", "value": 7.0 (optional)}
    """
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

@app.route('/api/sensors/ec/calibrate', methods=['POST'])
@api_endpoint
def api_calibrate_ec():
    """
    Calibrate EC sensor
    Body: {"point": "dry"|"single"|"low"|"high"|"clear", "value": 1413 (optional)}
    """
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

@app.route('/api/sensors/calibration/status', methods=['GET'])
@api_endpoint
def api_get_calibration_status():
    """Get calibration status for both sensors"""
    result = get_sensor_calibration_status()

    return jsonify(result)

# -----------------------------------------------------------------------------
# TANK MONITOR ENDPOINTS - Per-tank pH/EC Arduino monitors
# -----------------------------------------------------------------------------

@app.route('/api/tank-monitors', methods=['GET'])
@api_endpoint
def api_get_all_tank_monitors():
    """Get readings from all tank monitors"""
    readings = get_tank_monitor_readings()
    return jsonify({
        'success': True,
        'monitors': readings
    })

@app.route('/api/tank-monitors/<int:tank_id>', methods=['GET'])
@api_endpoint
def api_get_tank_monitor(tank_id):
    """Get readings from a specific tank monitor"""
    readings = get_tank_monitor_readings(tank_id)
    if 'error' in readings:
        return jsonify({
            'success': False,
            'error': readings['error']
        }), 404

    return jsonify({
        'success': True,
        'data': readings
    })

# -----------------------------------------------------------------------------
# EMERGENCY CONTROLS - Same as simple_gui.py
# -----------------------------------------------------------------------------

@app.route('/api/emergency/stop', methods=['POST'])
@api_endpoint
def api_emergency_stop():
    """Emergency stop all operations"""
    success = emergency_stop()
    
    return jsonify({
        'success': success,
        'message': "🚨 EMERGENCY STOP ACTIVATED 🚨" if success else "Emergency stop failed"
    })


# =============================================================================
# BATCH DOSING JOB - Server-side closed-loop fill + EC/pH dosing
# =============================================================================

@app.route('/api/job/batch/start', methods=['POST'])
@api_endpoint
def api_start_batch_job():
    """Start a closed-loop batch: fill to target, then dose EC and pH to setpoints.

    Body: {tank_id, target_gallons, recipe (nutrients.json key, e.g. 'veg_formula'),
           ec_target?, ph_target?, ec_tol?, ph_tol?}
    """
    import dosing_job

    data = request.get_json() or {}

    # --- tank ---
    try:
        tank_id = int(data.get('tank_id'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'tank_id required'}), 400
    tanks = getattr(config, 'TANKS', {})
    tank = tanks.get(tank_id)
    if not tank:
        return jsonify({'success': False, 'error': f'Unknown tank_id {tank_id}'}), 400

    # --- volume ---
    try:
        target_gallons = float(data.get('target_gallons'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'target_gallons required'}), 400
    capacity = tank.get('capacity_gallons', getattr(config, 'MAX_FLOW_GALLONS', 100))
    max_flow = getattr(config, 'MAX_FLOW_GALLONS', 100)
    if target_gallons < dosing_job.PRIME_GALLONS:
        return jsonify({'success': False, 'error':
                        f'target_gallons must be >= {dosing_job.PRIME_GALLONS:.0f} (circ-pump prime minimum)'}), 400
    if target_gallons > min(capacity, max_flow):
        return jsonify({'success': False, 'error':
                        f'target_gallons exceeds limit ({min(capacity, max_flow)} gal for tank {tank_id})'}), 400

    # --- recipe + pump map (from nutrients.json) ---
    nutrients_data = {}
    if os.path.exists('nutrients.json'):
        with open('nutrients.json', 'r') as f:
            nutrients_data = json.load(f)
    recipe_key = data.get('recipe', 'veg_formula')
    recipe = nutrients_data.get(recipe_key)
    if not recipe:
        return jsonify({'success': False, 'error': f'Unknown recipe "{recipe_key}"'}), 400
    pump_ids = nutrients_data.get('pump_name_to_id', {})
    missing = [n for n in recipe if n not in pump_ids]
    if missing:
        return jsonify({'success': False, 'error':
                        f'No pump mapping for: {", ".join(missing)}'}), 400

    cfg = dosing_job.BatchConfig(
        tank_id=tank_id,
        target_gallons=target_gallons,
        recipe=dict(recipe),
        pump_ids={n: int(pump_ids[n]) for n in recipe},
        fill_relay=tank['fill_relay'],
        mix_relays=list(tank['mix_relays']),
        flow_meter_id=int(data.get('flow_meter_id', 1)),
        ec_target=float(data.get('ec_target', dosing_job.DEFAULT_EC_TARGET)),
        ph_target=float(data.get('ph_target', dosing_job.DEFAULT_PH_TARGET)),
        ec_tol=float(data.get('ec_tol', dosing_job.DEFAULT_EC_TOL)),
        ph_tol=float(data.get('ph_tol', dosing_job.DEFAULT_PH_TOL)),
        advisory=bool(data.get('advisory', False)),
    )

    try:
        job = dosing_job.start_batch(cfg)
    except RuntimeError as e:
        return jsonify({'success': False, 'error': str(e)}), 409  # already running

    logger.info(f"Batch dosing job started for tank {tank_id}: {target_gallons} gal {recipe_key}")
    return jsonify({'success': True, 'message': 'Batch job started', 'job': job.snapshot()})


@app.route('/api/job/batch/status', methods=['GET'])
@api_endpoint
def api_batch_job_status():
    """Current batch job status (null if none has run)."""
    import dosing_job
    job = dosing_job.get_current()
    return jsonify({'success': True, 'job': job.snapshot() if job else None})


@app.route('/api/job/batch/abort', methods=['POST'])
@api_endpoint
def api_abort_batch_job():
    """Abort the running batch job and shut its hardware down safely."""
    import dosing_job
    aborted = dosing_job.abort_current()
    return jsonify({
        'success': aborted,
        'message': 'Batch job aborting' if aborted else 'No active batch job to abort'
    })


@app.route('/api/job/batch/ack', methods=['POST'])
@api_endpoint
def api_ack_batch_job():
    """Advisory mode: confirm the current recommended action so the job advances."""
    import dosing_job
    acked = dosing_job.ack_current()
    return jsonify({
        'success': acked,
        'message': 'Acknowledged' if acked else 'No pending action to acknowledge'
    })


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