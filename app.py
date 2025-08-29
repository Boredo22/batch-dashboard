#!/usr/bin/env python3
"""
Flask Application for Nutrient Mixing System - SIMPLIFIED VERSION
3-page mobile-friendly interface: Home (Operations), Settings, Testing
Following the working pattern from grower_web_app.py
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any

# Import the working FeedControlSystem directly
from main import FeedControlSystem
from config import (
    TANKS, VEG_FORMULA, BLOOM_FORMULA, FORMULA_TARGETS, PUMP_NAME_TO_ID,
    JOB_SETTINGS, get_tank_info, get_pump_name, get_available_pumps,
    get_available_relays, get_relay_name, MOCK_SETTINGS
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = 'nutrient_mixing_system_2024'

# Global system instance (like grower_web_app.py)
system = None
system_lock = threading.Lock()

def get_system():
    """Get or create the feed control system"""
    global system
    with system_lock:
        if system is None:
            try:
                system = FeedControlSystem(use_mock_flow=True)
                system.start()
                print("✓ Feed control system started")
            except Exception as e:
                print(f"✗ Failed to start system: {e}")
                return None
        return system

# =============================================================================
# DIRECT HARDWARE COMMAND FUNCTIONS (Working Pattern)
# =============================================================================

def control_relay(relay_id, state):
    """Control relay using working command format"""
    sys = get_system()
    if not sys:
        return False
    
    state_str = "ON" if state else "OFF"
    command = f"Start;Relay;{relay_id};{state_str};end"
    return sys.send_command(command)

def dispense_pump(pump_id, amount):
    """Dispense from pump using working command format"""
    sys = get_system()
    if not sys:
        return False
    
    command = f"Start;Dispense;{pump_id};{amount};end"
    return sys.send_command(command)

def stop_pump(pump_id):
    """Stop pump using working command format"""
    sys = get_system()
    if not sys:
        return False
    
    command = f"Start;Pump;{pump_id};X;end"
    return sys.send_command(command)

# =============================================================================
# ROUTES - Homepage (Operations)
# =============================================================================

@app.route('/')
def home():
    """Homepage - Tank operations interface"""
    return render_template('home.html')

@app.route('/api/status')
def get_status():
    """Get system status like the working GUI does"""
    sys = get_system()
    if not sys:
        return jsonify({'error': 'System not available'}), 500
    
    try:
        status = sys.get_system_status()
        
        # Format for web interface (copy grower_web_app.py pattern)
        formatted_status = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'system_running': status['running'],
            'relays': status.get('relays', {}),
            'pumps': status.get('pumps', {}),
            'flow_meters': status.get('flow_meters', {}),
            'ec_ph': status.get('ec_ph', {})
        }
        
        return jsonify(formatted_status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """Emergency stop using working FeedControlSystem"""
    try:
        sys = get_system()
        if not sys:
            return jsonify({'error': 'System not available'}), 500
        
        sys.emergency_stop()
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop activated'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# ROUTES - Settings Page
# =============================================================================

@app.route('/settings')
def settings():
    """Settings page - Configuration management"""
    return render_template('settings.html')

@app.route('/api/settings/formulas')
def get_formulas():
    """Get nutrient formulas"""
    try:
        return jsonify({
            'formulas': FORMULA_TARGETS,
            'pump_mapping': PUMP_NAME_TO_ID,
            'job_settings': JOB_SETTINGS
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/system')
def get_system_settings():
    """Get system settings"""
    try:
        return jsonify({
            'job_settings': JOB_SETTINGS,
            'mock_hardware': MOCK_SETTINGS,
            'tanks': TANKS,
            'available_pumps': get_available_pumps(),
            'available_relays': get_available_relays()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# ROUTES - Testing Page
# =============================================================================

@app.route('/testing')
def testing():
    """Testing page - Hardware testing and diagnostics"""
    return render_template('testing.html')

@app.route('/api/hardware/relay/<int:relay_id>/<action>', methods=['POST'])
def control_relay_endpoint(relay_id, action):
    """Control relay - matches working GUI functionality"""
    try:
        if action not in ['on', 'off']:
            return jsonify({'error': 'Invalid action'}), 400
        
        state = (action == 'on')
        success = control_relay(relay_id, state)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Relay {relay_id} turned {action.upper()}'
            })
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/pump/<int:pump_id>/dispense', methods=['POST'])
def dispense_pump_endpoint(pump_id):
    """Dispense from pump - matches working GUI functionality"""
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', 5.0))
        
        if not (0.5 <= amount <= 500):
            return jsonify({'error': 'Amount must be between 0.5 and 500 ml'}), 400
        
        success = dispense_pump(pump_id, amount)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Dispensing {amount}ml from pump {pump_id}'
            })
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/pump/<int:pump_id>/stop', methods=['POST'])
def stop_pump_endpoint(pump_id):
    """Stop pump using working command format"""
    try:
        success = stop_pump(pump_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Stopped pump {pump_id}'
            })
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/pump/<int:pump_id>/dispense', methods=['POST'])
def test_pump(pump_id):
    """Test pump dispensing using working command format"""
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', 5.0))
        
        if not (0.5 <= amount <= 50):
            return jsonify({'error': 'Amount must be between 0.5 and 50 ml'}), 400
        
        success = dispense_pump(pump_id, amount)
        
        if success:
            pump_name = get_pump_name(pump_id)
            return jsonify({
                'success': True,
                'message': f'Started dispensing {amount}ml from {pump_name}',
                'pump_id': pump_id,
                'amount': amount,
                'command_used': f'Start;Dispense;{pump_id};{amount};end'
            })
        else:
            return jsonify({'error': 'Failed to start pump'}), 500
            
    except Exception as e:
        logger.error(f"Error testing pump: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/relay/<int:relay_id>/<action>', methods=['POST'])
def test_relay(relay_id, action):
    """Test relay using working command format"""
    try:
        if action not in ['on', 'off']:
            return jsonify({'error': 'Invalid action'}), 400
        
        state = (action == 'on')
        success = control_relay(relay_id, state)
        
        if success:
            relay_name = get_relay_name(relay_id)
            return jsonify({
                'success': True,
                'message': f'Relay {relay_id} ({relay_name}) turned {action.upper()}',
                'relay_id': relay_id,
                'state': state,
                'command_used': f'Start;Relay;{relay_id};{action.upper()};end'
            })
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/status')
def get_test_status():
    """Get system status for testing page"""
    try:
        sys = get_system()
        if not sys:
            return jsonify({'error': 'System not available'}), 500
        
        status = sys.get_system_status()
        
        # Format for testing interface
        test_status = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'system_running': status['running'],
            'hardware_status': {
                'relays': {},
                'pumps': {},
                'sensors': status.get('ec_ph', {})
            }
        }
        
        # Format relay status with names
        relay_states = status.get('relays', {})
        for relay_id in get_available_relays():
            test_status['hardware_status']['relays'][relay_id] = {
                'name': get_relay_name(relay_id),
                'state': relay_states.get(relay_id, False)
            }
        
        # Format pump status with names  
        pumps = status.get('pumps', {})
        for pump_id in get_available_pumps():
            if pump_id in pumps:
                pump_info = pumps[pump_id]
                test_status['hardware_status']['pumps'][pump_id] = {
                    'name': get_pump_name(pump_id),
                    'dispensing': pump_info.get('is_dispensing', False),
                    'connected': pump_info.get('connected', False),
                    'calibrated': pump_info.get('calibrated', False)
                }
        
        return jsonify(test_status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# Tank Operation Routes (Simplified)
# =============================================================================

@app.route('/api/tank/<int:tank_id>/<action>', methods=['POST'])
def tank_operation(tank_id, action):
    """Simple tank operations using direct relay control"""
    try:
        if tank_id not in TANKS:
            return jsonify({'error': 'Invalid tank ID'}), 400
        
        tank_info = get_tank_info(tank_id)
        success = False
        
        if action == 'fill':
            fill_relay = tank_info.get('fill_relay')
            if fill_relay:
                success = control_relay(fill_relay, True)
        elif action == 'stop_fill':
            fill_relay = tank_info.get('fill_relay')
            if fill_relay:
                success = control_relay(fill_relay, False)
        elif action == 'mix':
            mix_relays = tank_info.get('mix_relays', [])
            for relay_id in mix_relays:
                control_relay(relay_id, True)
            success = len(mix_relays) > 0
        elif action == 'stop_mix':
            mix_relays = tank_info.get('mix_relays', [])
            for relay_id in mix_relays:
                control_relay(relay_id, False)
            success = len(mix_relays) > 0
        elif action == 'send':
            send_relay = tank_info.get('send_relay')
            if send_relay:
                success = control_relay(send_relay, True)
        elif action == 'stop_send':
            send_relay = tank_info.get('send_relay')
            if send_relay:
                success = control_relay(send_relay, False)
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Tank {tank_id} {action} completed'
            })
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# =============================================================================
# Application Startup
# =============================================================================

if __name__ == '__main__':
    print("🌱 Nutrient Mixing System - Simplified Flask Application")
    print("=" * 60)
    
    # Initialize system using simple pattern
    sys = get_system()
    if sys:
        print("✓ System initialized successfully")
        print("📱 Access the interface at: http://localhost:5000")
        print("   - Home: Tank operations")
        print("   - Settings: Configuration management") 
        print("   - Testing: Hardware diagnostics")
        print("🔧 Emergency stop available on all pages")
        
        try:
            # Run Flask app
            app.run(
                host='0.0.0.0',
                port=5000,
                debug=False,
                threaded=True
            )
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            if sys:
                sys.stop()
    else:
        print("✗ System initialization failed")
        exit(1)