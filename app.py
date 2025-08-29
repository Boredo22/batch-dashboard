#!/usr/bin/env python3
"""
Flask Application for Nutrient Mixing System - SIMPLIFIED VERSION
Fixed to work exactly like simple_gui.py but with HTTP endpoints
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any

# Import the working FeedControlSystem directly (like simple_gui.py)
from main import FeedControlSystem
from config import (
    TANKS, VEG_FORMULA, BLOOM_FORMULA, get_tank_info, get_pump_name, 
    get_available_pumps, get_available_relays, get_relay_name, 
    get_available_flow_meters, get_flow_meter_name, MOCK_SETTINGS
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = 'nutrient_mixing_system_2024'

# Global system instance - SIMPLE like simple_gui.py
system = None
system_lock = threading.Lock()

def get_system():
    """Get or create the feed control system (like simple_gui.py)"""
    global system
    with system_lock:
        if system is None:
            try:
                # Use same mock settings pattern as simple_gui
                use_mock_flow = MOCK_SETTINGS.get('flow_meters', False)
                system = FeedControlSystem(use_mock_flow=use_mock_flow)
                system.start()
                logger.info("✓ Feed control system started")
            except Exception as e:
                logger.error(f"✗ Failed to start system: {e}")
                return None
        return system

# =============================================================================
# DIRECT HARDWARE COMMAND FUNCTIONS (Copied from simple_gui.py pattern)
# =============================================================================

def control_relay(relay_id, state):
    """Control relay using exact same validation and command as simple_gui.py"""
    sys = get_system()
    if not sys:
        logger.error("System not available for relay control")
        return False
    
    # Same validation as simple_gui.py line 1055-1060
    if relay_id != 0 and relay_id not in get_available_relays():
        logger.error(f"Invalid relay ID: {relay_id}")
        return False
    
    # Exact same command format as simple_gui.py
    state_str = "ON" if state else "OFF"
    command = f"Start;Relay;{relay_id};{state_str};end"
    success = sys.send_command(command)
    
    if success:
        relay_name = get_relay_name(relay_id) if relay_id != 0 else "All Relays"
        action = "turned on" if state else "turned off"
        logger.info(f"{relay_name} {action}")
    else:
        logger.error(f"Failed to control relay {relay_id}")
    
    return success

def dispense_pump(pump_id, amount_ml):
    """Dispense from pump using exact same pattern as simple_gui.py"""
    sys = get_system()
    if not sys:
        logger.error("System not available for pump control")
        return False
    
    # Same validation as simple_gui.py line 1025-1035
    if pump_id not in get_available_pumps():
        logger.error(f"Invalid pump ID: {pump_id}")
        return False
    
    try:
        amount = int(amount_ml)
        if not (1 <= amount <= 9999):  # Same limits as simple_gui
            logger.error(f"Amount must be between 1 and 9999 ml, got: {amount}")
            return False
    except (ValueError, TypeError):
        logger.error(f"Invalid amount value: {amount_ml}")
        return False
    
    # Exact same command format as simple_gui.py line 1044
    command = f"Start;Dispense;{pump_id};{amount};end"
    success = sys.send_command(command)
    
    if success:
        pump_name = get_pump_name(pump_id)
        logger.info(f"Dispensing {amount}ml from {pump_name}")
    else:
        logger.error(f"Failed to start dispense from pump {pump_id}")
    
    return success

def stop_pump(pump_id):
    """Stop pump using exact same command as simple_gui.py"""
    sys = get_system()
    if not sys:
        logger.error("System not available for pump control")
        return False
    
    # Same validation 
    if pump_id not in get_available_pumps():
        logger.error(f"Invalid pump ID: {pump_id}")
        return False
    
    # Exact same command format as simple_gui.py line 1054
    command = f"Start;Pump;{pump_id};X;end"
    success = sys.send_command(command)
    
    if success:
        pump_name = get_pump_name(pump_id)
        logger.info(f"Stopped {pump_name}")
    else:
        logger.error(f"Failed to stop pump {pump_id}")
    
    return success

def start_flow(flow_id, gallons):
    """Start flow monitoring using same pattern as simple_gui.py"""
    sys = get_system()
    if not sys:
        return False
    
    # Same validation as simple_gui.py
    if flow_id not in get_available_flow_meters():
        logger.error(f"Invalid flow meter ID: {flow_id}")
        return False
    
    try:
        gal = int(gallons)
        if not (1 <= gal <= 300):  # Same limits as config MAX_FLOW_GALLONS
            logger.error(f"Gallons must be between 1 and 300, got: {gal}")
            return False
    except (ValueError, TypeError):
        logger.error(f"Invalid gallons value: {gallons}")
        return False
    
    # Same command format as simple_gui.py
    command = f"Start;StartFlow;{flow_id};{gal};220;end"
    success = sys.send_command(command)
    
    if success:
        meter_name = get_flow_meter_name(flow_id)
        logger.info(f"Started {meter_name} for {gal} gallons")
    
    return success

def stop_flow(flow_id):
    """Stop flow monitoring"""
    sys = get_system()
    if not sys:
        return False
    
    command = f"Start;StartFlow;{flow_id};0;end"
    success = sys.send_command(command)
    
    if success:
        meter_name = get_flow_meter_name(flow_id)
        logger.info(f"Stopped {meter_name}")
    
    return success

def emergency_stop():
    """Emergency stop using same method as simple_gui.py"""
    sys = get_system()
    if not sys:
        return False
    
    sys.emergency_stop()
    logger.warning("🚨 EMERGENCY STOP ACTIVATED 🚨")
    return True

def get_system_status():
    """Get system status using same method as simple_gui.py"""
    sys = get_system()
    if not sys:
        return {'error': 'System not available'}
    
    try:
        # Same status call as simple_gui.py
        status = sys.get_system_status()
        
        # Format for web interface
        formatted_status = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'system_running': status.get('running', False),
            'relays': status.get('relays', {}),
            'pumps': status.get('pumps', {}),
            'flow_meters': status.get('flow_meters', {}),
            'ec_ph': status.get('ec_ph', {})
        }
        
        return formatted_status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {'error': str(e)}

# =============================================================================
# FLASK ROUTES (Simple HTTP endpoints for the working commands)
# =============================================================================

@app.route('/')
def home():
    """Main dashboard"""
    return render_template('home.html', 
                         tanks=TANKS,
                         available_pumps=get_available_pumps(),
                         available_relays=get_available_relays(),
                         available_flow_meters=get_available_flow_meters())

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html',
                         veg_formula=VEG_FORMULA,
                         bloom_formula=BLOOM_FORMULA)

@app.route('/testing')
def testing():
    """Hardware testing page"""
    return render_template('testing.html',
                         available_pumps=get_available_pumps(),
                         available_relays=get_available_relays(),
                         available_flow_meters=get_available_flow_meters())

# =============================================================================
# API ENDPOINTS (Direct hardware control - working pattern)
# =============================================================================

@app.route('/api/status')
def api_status():
    """Get system status"""
    status = get_system_status()
    return jsonify(status)

@app.route('/api/relay/<int:relay_id>/<action>', methods=['POST'])
def api_relay_control(relay_id, action):
    """Control relay - exact same pattern as simple_gui button clicks"""
    try:
        if action not in ['on', 'off']:
            return jsonify({'error': 'Invalid action. Use on/off'}), 400
        
        state = (action == 'on')
        success = control_relay(relay_id, state)
        
        if success:
            relay_name = get_relay_name(relay_id) if relay_id != 0 else "All Relays"
            return jsonify({
                'success': True,
                'message': f'{relay_name} turned {action}',
                'relay_id': relay_id,
                'state': state
            })
        else:
            return jsonify({'error': f'Failed to turn {action} relay {relay_id}'}), 500
            
    except Exception as e:
        logger.error(f"Error controlling relay {relay_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pump/<int:pump_id>/dispense', methods=['POST'])
def api_pump_dispense(pump_id):
    """Dispense from pump - exact same pattern as simple_gui"""
    try:
        data = request.get_json()
        amount = data.get('amount') if data else request.form.get('amount')
        
        if not amount:
            return jsonify({'error': 'Amount required'}), 400
        
        success = dispense_pump(pump_id, amount)
        
        if success:
            pump_name = get_pump_name(pump_id)
            return jsonify({
                'success': True,
                'message': f'Dispensing {amount}ml from {pump_name}',
                'pump_id': pump_id,
                'amount': int(amount)
            })
        else:
            return jsonify({'error': f'Failed to dispense from pump {pump_id}'}), 500
            
    except Exception as e:
        logger.error(f"Error dispensing from pump {pump_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pump/<int:pump_id>/stop', methods=['POST'])
def api_pump_stop(pump_id):
    """Stop pump - exact same pattern as simple_gui"""
    try:
        success = stop_pump(pump_id)
        
        if success:
            pump_name = get_pump_name(pump_id)
            return jsonify({
                'success': True,
                'message': f'{pump_name} stopped',
                'pump_id': pump_id
            })
        else:
            return jsonify({'error': f'Failed to stop pump {pump_id}'}), 500
            
    except Exception as e:
        logger.error(f"Error stopping pump {pump_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/flow/<int:flow_id>/start', methods=['POST'])
def api_flow_start(flow_id):
    """Start flow monitoring"""
    try:
        data = request.get_json()
        gallons = data.get('gallons') if data else request.form.get('gallons')
        
        if not gallons:
            return jsonify({'error': 'Gallons required'}), 400
        
        success = start_flow(flow_id, gallons)
        
        if success:
            meter_name = get_flow_meter_name(flow_id)
            return jsonify({
                'success': True,
                'message': f'Started {meter_name} for {gallons} gallons',
                'flow_id': flow_id,
                'gallons': int(gallons)
            })
        else:
            return jsonify({'error': f'Failed to start flow meter {flow_id}'}), 500
            
    except Exception as e:
        logger.error(f"Error starting flow meter {flow_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/flow/<int:flow_id>/stop', methods=['POST'])
def api_flow_stop(flow_id):
    """Stop flow monitoring"""
    try:
        success = stop_flow(flow_id)
        
        if success:
            meter_name = get_flow_meter_name(flow_id)
            return jsonify({
                'success': True,
                'message': f'{meter_name} stopped',
                'flow_id': flow_id
            })
        else:
            return jsonify({'error': f'Failed to stop flow meter {flow_id}'}), 500
            
    except Exception as e:
        logger.error(f"Error stopping flow meter {flow_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency-stop', methods=['POST'])
def api_emergency_stop():
    """Emergency stop all operations"""
    try:
        success = emergency_stop()
        
        if success:
            return jsonify({
                'success': True,
                'message': '🚨 EMERGENCY STOP ACTIVATED 🚨'
            })
        else:
            return jsonify({'error': 'Failed to execute emergency stop'}), 500
            
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# SYSTEM CLEANUP
# =============================================================================

def cleanup_system():
    """Cleanup system resources"""
    global system
    try:
        if system:
            logger.info("Shutting down system...")
            system.stop()
            system = None
        logger.info("System cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

@app.teardown_appcontext
def close_system(error):
    """Clean up after request"""
    pass  # System stays running between requests

# =============================================================================
# MAIN APPLICATION STARTUP
# =============================================================================

def main():
    """Main entry point"""
    logger.info("Starting Nutrient Mixing System Flask App")
    
    # Initialize system on startup
    sys = get_system()
    if not sys:
        logger.error("Failed to initialize system")
        return
    
    try:
        # Run Flask app
        app.run(
            host='0.0.0.0',  # Listen on all interfaces for mobile access
            port=5000,
            debug=False,  # Set to True for development
            threaded=True
        )
    finally:
        cleanup_system()

if __name__ == '__main__':
    main()