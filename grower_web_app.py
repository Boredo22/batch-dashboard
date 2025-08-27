#!/usr/bin/env python3
"""
Simple Flask Web App for Grower Irrigation Control
Large touch-friendly interface for remote access
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import time
import json
from datetime import datetime

# Import our system
from main import FeedControlSystem
from config import (
    TANKS, RELAY_COMBOS, get_available_relays, get_available_pumps,
    get_relay_name, get_pump_name, get_tank_info
)

app = Flask(__name__)
CORS(app)

# Global system instance
system = None
system_lock = threading.Lock()

def get_system():
    """Get or create the feed control system"""
    global system
    with system_lock:
        if system is None:
            try:
                system = FeedControlSystem(use_mock_flow=True)  # Use mock for reliability
                system.start()
                print("✓ Feed control system started")
            except Exception as e:
                print(f"✗ Failed to start system: {e}")
                return None
        return system

@app.route('/')
def index():
    """Main grower interface"""
    return render_template('grower_interface.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    sys = get_system()
    if not sys:
        return jsonify({'error': 'System not available'}), 500
    
    try:
        status = sys.get_system_status()
        
        # Format for grower interface
        formatted_status = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'system_running': status['running'],
            'tanks': {},
            'relays': {},
            'ec_ph': status.get('ec_ph', {}),
            'pumps': {}
        }
        
        # Tank status based on relay states
        relay_states = status.get('relays', {})
        for tank_id, tank_info in TANKS.items():
            tank_status = {
                'name': tank_info['name'],
                'capacity': tank_info['capacity_gallons'],
                'filling': relay_states.get(tank_info.get('fill_relay'), False),
                'mixing': any(relay_states.get(r, False) for r in tank_info.get('mix_relays', [])),
                'sending': relay_states.get(tank_info.get('send_relay'), False)
            }
            formatted_status['tanks'][tank_id] = tank_status
        
        # Relay states with names
        for relay_id in get_available_relays():
            formatted_status['relays'][relay_id] = {
                'name': get_relay_name(relay_id),
                'state': relay_states.get(relay_id, False)
            }
        
        # Pump status
        pumps = status.get('pumps', {})
        for pump_id in get_available_pumps():
            if pump_id in pumps:
                pump_info = pumps[pump_id]
                formatted_status['pumps'][pump_id] = {
                    'name': get_pump_name(pump_id),
                    'dispensing': pump_info.get('is_dispensing', False),
                    'volume': pump_info.get('current_volume', 0),
                    'target': pump_info.get('target_volume', 0)
                }
        
        return jsonify(formatted_status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tank/<int:tank_id>/<action>', methods=['POST'])
def tank_action(tank_id, action):
    """Control tank operations"""
    sys = get_system()
    if not sys:
        return jsonify({'error': 'System not available'}), 500
    
    if tank_id not in TANKS:
        return jsonify({'error': 'Invalid tank'}), 400
    
    tank_info = get_tank_info(tank_id)
    success = False
    
    try:
        if action == 'fill':
            # Turn on fill relay
            fill_relay = tank_info.get('fill_relay')
            if fill_relay:
                command = f"Start;Relay;{fill_relay};ON;end"
                success = sys.send_command(command)
        
        elif action == 'stop_fill':
            # Turn off fill relay
            fill_relay = tank_info.get('fill_relay')
            if fill_relay:
                command = f"Start;Relay;{fill_relay};OFF;end"
                success = sys.send_command(command)
        
        elif action == 'mix':
            # Turn on mix relays
            mix_relays = tank_info.get('mix_relays', [])
            for relay_id in mix_relays:
                command = f"Start;Relay;{relay_id};ON;end"
                sys.send_command(command)
            success = len(mix_relays) > 0
        
        elif action == 'stop_mix':
            # Turn off mix relays
            mix_relays = tank_info.get('mix_relays', [])
            for relay_id in mix_relays:
                command = f"Start;Relay;{relay_id};OFF;end"
                sys.send_command(command)
            success = len(mix_relays) > 0
        
        elif action == 'send':
            # Turn on send relay
            send_relay = tank_info.get('send_relay')
            if send_relay:
                command = f"Start;Relay;{send_relay};ON;end"
                success = sys.send_command(command)
        
        elif action == 'stop_send':
            # Turn off send relay
            send_relay = tank_info.get('send_relay')
            if send_relay:
                command = f"Start;Relay;{send_relay};OFF;end"
                success = sys.send_command(command)
        
        elif action == 'stop_all':
            # Stop all operations for this tank
            all_relays = []
            if tank_info.get('fill_relay'):
                all_relays.append(tank_info['fill_relay'])
            all_relays.extend(tank_info.get('mix_relays', []))
            if tank_info.get('send_relay'):
                all_relays.append(tank_info['send_relay'])
            
            for relay_id in all_relays:
                command = f"Start;Relay;{relay_id};OFF;end"
                sys.send_command(command)
            success = len(all_relays) > 0
        
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        if success:
            return jsonify({'success': True, 'message': f'Tank {tank_id} {action} completed'})
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/relay/<int:relay_id>/<state>', methods=['POST'])
def control_relay(relay_id, state):
    """Control individual relay"""
    sys = get_system()
    if not sys:
        return jsonify({'error': 'System not available'}), 500
    
    if relay_id not in get_available_relays():
        return jsonify({'error': 'Invalid relay'}), 400
    
    if state not in ['on', 'off']:
        return jsonify({'error': 'Invalid state'}), 400
    
    try:
        state_str = "ON" if state == 'on' else "OFF"
        command = f"Start;Relay;{relay_id};{state_str};end"
        success = sys.send_command(command)
        
        if success:
            return jsonify({'success': True, 'message': f'Relay {relay_id} turned {state_str}'})
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """Emergency stop all operations"""
    sys = get_system()
    if not sys:
        return jsonify({'error': 'System not available'}), 500
    
    try:
        sys.emergency_stop()
        return jsonify({'success': True, 'message': 'Emergency stop activated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pump/<int:pump_id>/dispense', methods=['POST'])
def dispense_pump(pump_id):
    """Dispense from pump"""
    sys = get_system()
    if not sys:
        return jsonify({'error': 'System not available'}), 500
    
    if pump_id not in get_available_pumps():
        return jsonify({'error': 'Invalid pump'}), 400
    
    try:
        data = request.get_json()
        amount = float(data.get('amount', 10.0))
        
        if not (0.5 <= amount <= 500):  # Reasonable limits for grower use
            return jsonify({'error': 'Amount must be between 0.5 and 500 ml'}), 400
        
        command = f"Start;Dispense;{pump_id};{amount};end"
        success = sys.send_command(command)
        
        if success:
            return jsonify({'success': True, 'message': f'Dispensing {amount}ml from {get_pump_name(pump_id)}'})
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pump/<int:pump_id>/stop', methods=['POST'])
def stop_pump(pump_id):
    """Stop pump"""
    sys = get_system()
    if not sys:
        return jsonify({'error': 'System not available'}), 500
    
    if pump_id not in get_available_pumps():
        return jsonify({'error': 'Invalid pump'}), 400
    
    try:
        command = f"Start;Pump;{pump_id};X;end"
        success = sys.send_command(command)
        
        if success:
            return jsonify({'success': True, 'message': f'Stopped {get_pump_name(pump_id)}'})
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌱 Grower Web Control Starting...")
    print("📱 Access from your phone/tablet at: http://[raspberry-pi-ip]:5000")
    print("🔧 Emergency stop available on all pages")
    
    # Create templates directory if it doesn't exist
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)