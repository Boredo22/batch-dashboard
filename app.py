#!/usr/bin/env python3
"""
Flask API Server for Nutrient Mixing System
Provides REST API endpoints for Svelte frontend
Uses hardware_comms.py for reliable hardware control like simple_gui.py
"""

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
    all_relays_off, cleanup_hardware, start_ec_ph, stop_ec_ph
)

# Import configuration constants (if needed for validation)
try:
    from config import MIN_PUMP_VOLUME_ML, MAX_PUMP_VOLUME_ML, MAX_FLOW_GALLONS
except ImportError:
    # Fallback constants
    MIN_PUMP_VOLUME_ML = 1
    MAX_PUMP_VOLUME_ML = 100
    MAX_FLOW_GALLONS = 50

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
        
        return jsonify({
            'success': True,
            'status': status,
            'hardware': hardware,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # Add data in the format expected by Dashboard.svelte  
            'relays': [{'id': rid, 'name': hardware['relays']['names'].get(rid, f'Relay {rid}'), 'state': status['relays'].get(str(rid), False)} 
                      for rid in hardware['relays']['ids']],
            'pumps': [{'id': pid, 'name': hardware['pumps']['names'].get(pid, f'Pump {pid}'), 'status': 'stopped'} 
                     for pid in hardware['pumps']['ids']],
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

def initialize_app():
    """Initialize the application"""
    logger.info("Starting Flask application...")
    
    # Test hardware communications
    try:
        status = get_system_status()
        if status.get('system_ready'):
            logger.info("✓ Hardware communications ready")
        else:
            logger.warning(f"⚠ Hardware system not fully ready: {status}")
    except Exception as e:
        logger.error(f"✗ Hardware initialization error: {e}")
    
    logger.info("Flask application initialized")

if __name__ == '__main__':
    initialize_app()
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5000,       # Default Flask port
        debug=True,      # Enable debug mode for development
        threaded=True    # Handle multiple requests
    )