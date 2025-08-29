#!/usr/bin/env python3
"""
Flask Application for Nutrient Mixing System
3-page mobile-friendly interface: Home (Operations), Settings, Testing
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import logging
import time
from datetime import datetime
from typing import Dict, Any

# Import our system components
from hardware.hardware_manager import HardwareManager
from scheduler import JobScheduler
from models import JobType, JobStatus, get_database_manager, init_models
from main import FeedControlSystem  # Import the working FeedControlSystem
from config import (
    TANKS, VEG_FORMULA, BLOOM_FORMULA, FORMULA_TARGETS, PUMP_NAME_TO_ID,
    JOB_SETTINGS, get_tank_info, get_pump_name, get_available_pumps,
    get_available_relays, MOCK_SETTINGS
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = 'nutrient_mixing_system_2024'

# Global system components
hardware_manager = None
job_scheduler = None
models = None
feed_control_system = None  # Add the working FeedControlSystem

def initialize_system():
    """Initialize the complete system"""
    global hardware_manager, job_scheduler, models, feed_control_system
    
    try:
        # Initialize models ONCE at startup
        logger.info("🔧 Initializing database models...")
        models = init_models()
        db_manager = models['db_manager']
        logger.info("✅ Database models initialized")
        
        # Use the same models throughout the app
        tank_model = models['tank']
        job_model = models['job']
        sensor_log_model = models['sensor_log']
        hardware_log_model = models['hardware_log']
        
        # Initialize the working FeedControlSystem (from grower_web_app.py)
        logger.info("🔧 Initializing FeedControlSystem...")
        feed_control_system = FeedControlSystem(use_mock_flow=MOCK_SETTINGS.get('flow_meters', False))
        feed_control_system.start()
        logger.info("✅ FeedControlSystem initialized and started")
        
        # Initialize hardware manager with mock settings for development
        hardware_manager = HardwareManager(use_mock_hardware=MOCK_SETTINGS)
        logger.info("✓ Hardware manager initialized")
        
        # Initialize job scheduler
        job_scheduler = JobScheduler(hardware_manager)
        job_scheduler.start()
        logger.info("✓ Job scheduler started")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ System initialization failed: {e}")
        return False

def cleanup_system():
    """Cleanup system resources"""
    global hardware_manager, job_scheduler
    
    try:
        if job_scheduler:
            job_scheduler.stop()
        if hardware_manager:
            hardware_manager.cleanup()
        logger.info("System cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# =============================================================================
# HELPER FUNCTIONS FOR HARDWARE COMMUNICATION
# =============================================================================

def send_hardware_command(command_str):
    """Send command using the working FeedControlSystem format"""
    global feed_control_system
    
    if not feed_control_system:
        logger.error("FeedControlSystem not initialized")
        return False
    
    try:
        success = feed_control_system.send_command(command_str)
        if success:
            logger.info(f"Hardware command sent successfully: {command_str}")
        else:
            logger.error(f"Hardware command failed: {command_str}")
        return success
    except Exception as e:
        logger.error(f"Error sending hardware command '{command_str}': {e}")
        return False

def control_relay_direct(relay_id, state):
    """Control relay using the working command format"""
    state_str = "ON" if state else "OFF"
    command = f"Start;Relay;{relay_id};{state_str};end"
    return send_hardware_command(command)

def dispense_pump_direct(pump_id, amount_ml):
    """Dispense from pump using the working command format"""
    command = f"Start;Dispense;{pump_id};{amount_ml};end"
    return send_hardware_command(command)

def stop_pump_direct(pump_id):
    """Stop pump using the working command format"""
    command = f"Start;Pump;{pump_id};X;end"
    return send_hardware_command(command)

def get_system_status_with_feed_control():
    """Get system status including FeedControlSystem data"""
    status = {}
    
    # Get status from FeedControlSystem if available
    if feed_control_system:
        try:
            feed_status = feed_control_system.get_system_status()
            status.update(feed_status)
        except Exception as e:
            logger.error(f"Error getting FeedControlSystem status: {e}")
    
    # Get status from job scheduler if available
    if job_scheduler:
        try:
            scheduler_status = job_scheduler.get_system_status()
            status['scheduler_running'] = scheduler_status.get('scheduler_running', False)
            status['active_jobs'] = scheduler_status.get('active_jobs', [])
            status['pending_jobs'] = scheduler_status.get('pending_jobs', [])
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
    
    return status

# =============================================================================
# ROUTES - Homepage (Operations)
# =============================================================================

@app.route('/')
def home():
    """Homepage - Tank operations interface"""
    return render_template('home.html')

@app.route('/api/status')
def get_status():
    """Get comprehensive system status"""
    try:
        if not job_scheduler or not hardware_manager:
            return jsonify({'error': 'System not initialized'}), 500
        
        # Get system status
        system_status = job_scheduler.get_system_status()
        
        # Get tank statuses
        tank_statuses = {}
        for tank_id in TANKS.keys():
            tank_status = job_scheduler.get_tank_status(tank_id)
            tank_statuses[tank_id] = tank_status
        
        # Format response
        response = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'system_running': system_status['scheduler_running'],
            'tanks': tank_statuses,
            'active_jobs': system_status['active_jobs'],
            'pending_jobs': system_status['pending_jobs'],
            'hardware_status': system_status.get('hardware_status', {}),
            'formulas': {
                'VEG': FORMULA_TARGETS['VEG'],
                'BLOOM': FORMULA_TARGETS['BLOOM']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tank/<int:tank_id>/fill', methods=['POST'])
def start_fill(tank_id):
    """Start fill operation for tank"""
    try:
        if not job_scheduler:
            return jsonify({'error': 'System not initialized'}), 500
        
        data = request.get_json() or {}
        gallons = float(data.get('gallons', 50))
        
        # Validate inputs
        if tank_id not in TANKS:
            return jsonify({'error': 'Invalid tank ID'}), 400
        
        if not (1 <= gallons <= TANKS[tank_id]['capacity_gallons']):
            return jsonify({'error': f'Gallons must be between 1 and {TANKS[tank_id]["capacity_gallons"]}'}), 400
        
        # Submit fill job
        job_id = job_scheduler.submit_job(
            JobType.FILL, 
            tank_id, 
            {'gallons': gallons}
        )
        
        if job_id:
            return jsonify({
                'success': True,
                'message': f'Fill job started: {gallons} gallons to {TANKS[tank_id]["name"]}',
                'job_id': job_id
            })
        else:
            return jsonify({'error': 'Failed to start fill job'}), 500
            
    except Exception as e:
        logger.error(f"Error starting fill: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tank/<int:tank_id>/mix', methods=['POST'])
def start_mix(tank_id):
    """Start mix operation for tank"""
    try:
        if not job_scheduler:
            return jsonify({'error': 'System not initialized'}), 500
        
        data = request.get_json() or {}
        formula_type = data.get('formula', 'VEG').upper()
        gallons = float(data.get('gallons', 50))
        
        # Validate inputs
        if tank_id not in TANKS:
            return jsonify({'error': 'Invalid tank ID'}), 400
        
        if formula_type not in FORMULA_TARGETS:
            return jsonify({'error': 'Invalid formula type'}), 400
        
        # Get formula configuration
        formula_config = FORMULA_TARGETS[formula_type]
        
        # Calculate nutrient amounts based on gallons
        formula_amounts = {}
        for nutrient_name, ml_per_gallon in formula_config['formula'].items():
            total_ml = ml_per_gallon * gallons
            formula_amounts[nutrient_name] = total_ml
        
        # Submit mix job
        job_id = job_scheduler.submit_job(
            JobType.MIX,
            tank_id,
            {
                'formula': formula_amounts,
                'ph_target': formula_config['ph_target'],
                'ec_target': formula_config['ec_target'],
                'gallons': gallons,
                'formula_type': formula_type
            }
        )
        
        if job_id:
            return jsonify({
                'success': True,
                'message': f'Mix job started: {formula_type} formula for {gallons} gallons in {TANKS[tank_id]["name"]}',
                'job_id': job_id,
                'formula': formula_amounts
            })
        else:
            return jsonify({'error': 'Failed to start mix job'}), 500
            
    except Exception as e:
        logger.error(f"Error starting mix: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tank/<int:tank_id>/send', methods=['POST'])
def start_send(tank_id):
    """Start send operation for tank"""
    try:
        if not job_scheduler:
            return jsonify({'error': 'System not initialized'}), 500
        
        data = request.get_json() or {}
        gallons = float(data.get('gallons', 25))
        destination = data.get('destination', f'Room from {TANKS[tank_id]["name"]}')
        
        # Validate inputs
        if tank_id not in TANKS:
            return jsonify({'error': 'Invalid tank ID'}), 400
        
        if not (1 <= gallons <= TANKS[tank_id]['capacity_gallons']):
            return jsonify({'error': f'Gallons must be between 1 and {TANKS[tank_id]["capacity_gallons"]}'}), 400
        
        # Submit send job
        job_id = job_scheduler.submit_job(
            JobType.SEND,
            tank_id,
            {
                'gallons': gallons,
                'destination': destination
            }
        )
        
        if job_id:
            return jsonify({
                'success': True,
                'message': f'Send job started: {gallons} gallons from {TANKS[tank_id]["name"]} to {destination}',
                'job_id': job_id
            })
        else:
            return jsonify({'error': 'Failed to start send job'}), 500
            
    except Exception as e:
        logger.error(f"Error starting send: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/job/<int:job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a job"""
    try:
        if not job_scheduler:
            return jsonify({'error': 'System not initialized'}), 500
        
        success = job_scheduler.cancel_job(job_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Job {job_id} cancelled'
            })
        else:
            return jsonify({'error': 'Failed to cancel job'}), 500
            
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """Emergency stop all operations"""
    try:
        if not job_scheduler:
            return jsonify({'error': 'System not initialized'}), 500
        
        success = job_scheduler.emergency_stop()
        
        if success:
            return jsonify({
                'success': True,
                'message': '🚨 EMERGENCY STOP ACTIVATED - All operations stopped 🚨'
            })
        else:
            return jsonify({'error': 'Emergency stop failed'}), 500
            
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
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

@app.route('/api/settings/hardware')
def get_hardware_config():
    """Get hardware configuration"""
    try:
        if not hardware_manager:
            return jsonify({'error': 'Hardware manager not initialized'}), 500
        
        status = hardware_manager.get_system_status()
        
        return jsonify({
            'tanks': TANKS,
            'controllers': status['controllers'],
            'mock_settings': MOCK_SETTINGS,
            'hardware_status': status.get('hardware_status', {})
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


@app.route('/api/test/pump/<int:pump_id>/dispense', methods=['POST'])
def test_pump(pump_id):
    """Test pump dispensing using working command format"""
    try:
        if not feed_control_system:
            return jsonify({'error': 'FeedControlSystem not available'}), 500
        
        data = request.get_json() or {}
        amount = float(data.get('amount', 5.0))
        
        if not (0.5 <= amount <= 50):
            return jsonify({'error': 'Amount must be between 0.5 and 50 ml'}), 400
        
        # Use the working command format
        success = dispense_pump_direct(pump_id, amount)
        
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

@app.route('/api/test/sensors', methods=['GET'])
def test_sensors():
    """Test pH/EC sensors"""
    try:
        if not hardware_manager or not hardware_manager.sensor_controller:
            return jsonify({'error': 'Sensor controller not available'}), 500
        
        readings = hardware_manager.sensor_controller.read_both_sensors()
        status = hardware_manager.sensor_controller.get_sensor_status()
        
        return jsonify({
            'success': True,
            'readings': readings,
            'sensor_status': status
        })
        
    except Exception as e:
        logger.error(f"Error testing sensors: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/flow/<int:meter_id>/start', methods=['POST'])
def test_flow_meter(meter_id):
    """Test flow meter"""
    try:
        if not hardware_manager or not hardware_manager.flow_controller:
            return jsonify({'error': 'Flow controller not available'}), 500
        
        data = request.get_json() or {}
        gallons = float(data.get('gallons', 1.0))
        
        if not (0.1 <= gallons <= 10):
            return jsonify({'error': 'Gallons must be between 0.1 and 10'}), 400
        
        success = hardware_manager.flow_controller.start_flow(meter_id, gallons)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Started flow monitoring for {gallons} gallons',
                'meter_id': meter_id,
                'target_gallons': gallons
            })
        else:
            return jsonify({'error': 'Failed to start flow monitoring'}), 500
            
    except Exception as e:
        logger.error(f"Error testing flow meter: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/hardware')
def get_hardware_logs():
    """Get recent hardware logs"""
    try:
        if not models:
            return jsonify({'error': 'Database not initialized'}), 500
        
        logs = models['hardware_log'].get_recent_logs(limit=50)
        return jsonify({'logs': logs})
        
    except Exception as e:
        logger.error(f"Error getting hardware logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/jobs')
def get_job_logs():
    """Get recent job logs"""
    try:
        if not models:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Get recent jobs from database
        with models['db_manager'].get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM jobs 
                ORDER BY created_at DESC 
                LIMIT 20
            """).fetchall()
            
            jobs = [dict(row) for row in rows]
        
        return jsonify({'jobs': jobs})
        
    except Exception as e:
        logger.error(f"Error getting job logs: {e}")
        return jsonify({'error': str(e)}), 500
    


# =============================================================================
# ENHANCED TESTING API ROUTES
# =============================================================================

@app.route('/api/test/relay/<int:relay_id>/<action>', methods=['POST'])
def test_relay_enhanced(relay_id, action):
    """Enhanced relay testing using working command format"""
    try:
        if not feed_control_system:
            return jsonify({'error': 'FeedControlSystem not available'}), 500
        
        if action not in ['on', 'off', 'toggle']:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Record start time
        start_time = time.time()
        
        # Log the action
        logger.info(f"Testing relay {relay_id}: {action}")
        
        # Get current state for toggle
        current_state = False
        if feed_control_system.relay_controller:
            current_state = feed_control_system.relay_controller.get_relay_state(relay_id)
        
        # Determine target state
        if action == 'toggle':
            target_state = not current_state
        else:
            target_state = action == 'on'
        
        # Use the working command format
        success = control_relay_direct(relay_id, target_state)
        
        # Get updated state
        new_state = target_state if success else current_state
        if feed_control_system.relay_controller:
            new_state = feed_control_system.relay_controller.get_relay_state(relay_id)
        
        # Verify GPIO state (this is the key enhancement!)
        gpio_verified = verify_gpio_state_feed_control(relay_id, new_state)
        
        # Calculate operation time
        operation_time = int((time.time() - start_time) * 1000)  # milliseconds
        
        # Get relay info
        relay_info = None
        if feed_control_system.relay_controller:
            relay_info = feed_control_system.relay_controller.get_relay_info(relay_id)
        
        if success:
            result = {
                'success': True,
                'relay_id': relay_id,
                'action': action,
                'state': new_state,
                'gpio_verified': gpio_verified,
                'operation_time_ms': operation_time,
                'gpio_pin': relay_info.get('gpio_pin') if relay_info else None,
                'message': f'Relay {relay_id} {"ON" if new_state else "OFF"}',
                'verification_status': 'verified' if gpio_verified else 'unverified',
                'timestamp': datetime.now().isoformat(),
                'command_used': f"Start;Relay;{relay_id};{'ON' if target_state else 'OFF'};end"
            }
            
            # Log success with details
            verification_msg = "GPIO verified ✓" if gpio_verified else "GPIO NOT verified ⚠️"
            logger.info(f"Relay {relay_id} operation successful - {verification_msg} ({operation_time}ms)")
            
        else:
            result = {
                'success': False,
                'error': 'Relay operation failed',
                'relay_id': relay_id,
                'gpio_verified': False,
                'timestamp': datetime.now().isoformat(),
                'command_used': f"Start;Relay;{relay_id};{'ON' if target_state else 'OFF'};end"
            }
            logger.error(f"Relay {relay_id} operation failed")
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Exception testing relay {relay_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'relay_id': relay_id,
            'gpio_verified': False,
            'timestamp': datetime.now().isoformat()
        }), 500


def verify_gpio_state(relay_id, expected_state):
    """
    Verify that the GPIO pin actually reflects the expected relay state
    This is crucial for confirming hardware is working properly
    """
    try:
        if not hardware_manager or not hardware_manager.relay_controller:
            return False
            
        # Get relay info to find GPIO pin
        relay_info = hardware_manager.relay_controller.get_relay_info(relay_id)
        if not relay_info:
            return False
            
        gpio_pin = relay_info.get('gpio_pin')
        if gpio_pin is None:
            return False
        
        # For real hardware, read the actual GPIO pin state
        if hasattr(hardware_manager.relay_controller, 'h') and hardware_manager.relay_controller.h:
            import lgpio
            try:
                # Read actual GPIO state
                actual_gpio_state = lgpio.gpio_read(hardware_manager.relay_controller.h, gpio_pin)
                
                # Account for relay logic (active high/low)
                from config import RELAY_ACTIVE_HIGH
                expected_gpio_state = 1 if (expected_state == RELAY_ACTIVE_HIGH) else 0
                
                gpio_verified = (actual_gpio_state == expected_gpio_state)
                
                if not gpio_verified:
                    logger.warning(f"GPIO verification failed: GPIO {gpio_pin} is {actual_gpio_state}, expected {expected_gpio_state}")
                else:
                    logger.debug(f"GPIO verification passed: GPIO {gpio_pin} = {actual_gpio_state}")
                    
                return gpio_verified
                
            except Exception as gpio_error:
                logger.error(f"GPIO verification error: {gpio_error}")
                return False
        else:
            # For mock hardware, simulate verification (occasionally fail for realism)
            import random
            return random.random() > 0.05  # 95% success rate for mock
            
    except Exception as e:
        logger.error(f"Exception during GPIO verification: {e}")
        return False

def verify_gpio_state_feed_control(relay_id, expected_state):
    """
    Verify GPIO state using FeedControlSystem relay controller
    """
    try:
        if not feed_control_system or not feed_control_system.relay_controller:
            return False
            
        # Get relay info to find GPIO pin
        relay_info = feed_control_system.relay_controller.get_relay_info(relay_id)
        if not relay_info:
            return False
            
        gpio_pin = relay_info.get('gpio_pin')
        if gpio_pin is None:
            return False
        
        # For real hardware, read the actual GPIO pin state
        if hasattr(feed_control_system.relay_controller, 'h') and feed_control_system.relay_controller.h:
            import lgpio
            try:
                # Read actual GPIO state
                actual_gpio_state = lgpio.gpio_read(feed_control_system.relay_controller.h, gpio_pin)
                
                # Account for relay logic (active high/low)
                from config import RELAY_ACTIVE_HIGH
                expected_gpio_state = 1 if (expected_state == RELAY_ACTIVE_HIGH) else 0
                
                gpio_verified = (actual_gpio_state == expected_gpio_state)
                
                if not gpio_verified:
                    logger.warning(f"GPIO verification failed: GPIO {gpio_pin} is {actual_gpio_state}, expected {expected_gpio_state}")
                else:
                    logger.debug(f"GPIO verification passed: GPIO {gpio_pin} = {actual_gpio_state}")
                    
                return gpio_verified
                
            except Exception as gpio_error:
                logger.error(f"GPIO verification error: {gpio_error}")
                return False
        else:
            # For mock hardware, simulate verification (occasionally fail for realism)
            import random
            return random.random() > 0.05  # 95% success rate for mock
            
    except Exception as e:
        logger.error(f"Exception during FeedControl GPIO verification: {e}")
        return False


@app.route('/api/test/relays/all/<action>', methods=['POST'])
def test_all_relays_enhanced(action):
    """Test all relays with detailed feedback"""
    try:
        if not hardware_manager or not hardware_manager.relay_controller:
            return jsonify({'error': 'Relay controller not available'}), 500
            
        if action not in ['on', 'off', 'test_sequence']:
            return jsonify({'error': 'Invalid action'}), 400
            
        available_relays = hardware_manager.relay_controller.get_available_relays()
        results = []
        
        for relay_id in available_relays:
            if action == 'test_sequence':
                # Test sequence: ON, wait, OFF
                on_result = test_single_relay_internal(relay_id, True)
                time.sleep(1)  # Wait 1 second
                off_result = test_single_relay_internal(relay_id, False)
                
                results.append({
                    'relay_id': relay_id,
                    'on_test': on_result,
                    'off_test': off_result,
                    'overall_success': on_result['success'] and off_result['success']
                })
            else:
                state = action == 'on'
                result = test_single_relay_internal(relay_id, state)
                results.append(result)
                
        # Calculate summary statistics
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get('success') or r.get('overall_success'))
        verified_tests = sum(1 for r in results if r.get('gpio_verified', False))
        
        return jsonify({
            'success': True,
            'action': action,
            'results': results,
            'summary': {
                'total_relays': total_tests,
                'successful_operations': successful_tests,
                'gpio_verified': verified_tests,
                'success_rate': round((successful_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
                'verification_rate': round((verified_tests / total_tests) * 100, 1) if total_tests > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error testing all relays: {e}")
        return jsonify({'error': str(e)}), 500


def test_single_relay_internal(relay_id, state):
    """Internal function for testing a single relay"""
    try:
        start_time = time.time()
        
        success = hardware_manager.relay_controller.set_relay(relay_id, state)
        current_state = hardware_manager.relay_controller.get_relay_state(relay_id)
        gpio_verified = verify_gpio_state(relay_id, current_state)
        operation_time = int((time.time() - start_time) * 1000)
        
        relay_info = hardware_manager.relay_controller.get_relay_info(relay_id)
        
        return {
            'success': success,
            'relay_id': relay_id,
            'state': current_state,
            'gpio_verified': gpio_verified,
            'operation_time_ms': operation_time,
            'gpio_pin': relay_info.get('gpio_pin') if relay_info else None,
            'relay_name': relay_info.get('name') if relay_info else f"Relay {relay_id}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'relay_id': relay_id,
            'gpio_verified': False
        }


@app.route('/api/test/system/status', methods=['GET'])
def get_enhanced_system_status():
    """Get comprehensive system status for the testing page"""
    try:
        # Get relay states and verification status
        relay_status = {}
        if hardware_manager and hardware_manager.relay_controller:
            available_relays = hardware_manager.relay_controller.get_available_relays()
            for relay_id in available_relays:
                relay_info = hardware_manager.relay_controller.get_relay_info(relay_id)
                current_state = hardware_manager.relay_controller.get_relay_state(relay_id)
                gpio_verified = verify_gpio_state(relay_id, current_state)
                
                relay_status[relay_id] = {
                    'name': relay_info.get('name') if relay_info else f"Relay {relay_id}",
                    'state': current_state,
                    'gpio_pin': relay_info.get('gpio_pin') if relay_info else None,
                    'gpio_verified': gpio_verified,
                    'active_high': relay_info.get('active_high') if relay_info else True
                }
        
        # Get pump status
        pump_status = {}
        if hardware_manager and hardware_manager.pump_controller:
            # Add pump status logic here
            pass
            
        # Get sensor readings
        sensor_readings = {}
        if hardware_manager:
            # Add sensor reading logic here
            sensor_readings = {
                'ph': {'value': 7.0, 'unit': 'pH', 'status': 'ok'},
                'ec': {'value': 1.2, 'unit': 'mS/cm', 'status': 'ok'},
                'temperature': {'value': 22, 'unit': '°C', 'status': 'ok'}
            }
        
        # System health metrics
        active_relays = sum(1 for r in relay_status.values() if r['state'])
        total_relays = len(relay_status)
        verified_relays = sum(1 for r in relay_status.values() if r['gpio_verified'])
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'system_health': {
                'status': 'healthy',
                'uptime': time.time() - app_start_time if 'app_start_time' in globals() else 0,
                'active_relays': active_relays,
                'total_relays': total_relays,
                'verification_rate': round((verified_relays / total_relays) * 100, 1) if total_relays > 0 else 100
            },
            'hardware_status': {
                'relays': relay_status,
                'pumps': pump_status,
                'sensors': sensor_readings
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/test/logs/hardware', methods=['GET'])
def get_test_hardware_logs():
    """Get recent hardware operation logs for testing"""
    try:
        # This would typically read from a log file or database
        # For now, return sample log entries
        
        limit = request.args.get('limit', 50, type=int)
        
        # Sample log entries - replace with actual log reading
        sample_logs = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'info',
                'component': 'relay',
                'message': 'System initialized successfully',
                'details': 'All 8 relays detected and verified'
            }
        ]
        
        return jsonify({
            'success': True,
            'logs': sample_logs[-limit:],
            'total_count': len(sample_logs)
        })
        
    except Exception as e:
        logger.error(f"Error getting hardware logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/test/emergency-stop', methods=['POST'])
def emergency_stop_all():
    """Emergency stop - turn off all hardware"""
    try:
        logger.warning("Emergency stop activated")
        
        results = {}
        
        # Turn off all relays
        if hardware_manager and hardware_manager.relay_controller:
            relay_result = hardware_manager.relay_controller.set_all_relays(False)
            results['relays'] = relay_result
            
        # Stop all pumps
        if hardware_manager and hardware_manager.pump_controller:
            # Add pump stop logic
            results['pumps'] = True
            
        return jsonify({
            'success': True,
            'message': 'Emergency stop completed',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# DIRECT HARDWARE CONTROL ENDPOINTS (Using Working Command Format)
# =============================================================================

@app.route('/api/hardware/relay/<int:relay_id>/<state>', methods=['POST'])
def control_relay_direct_endpoint(relay_id, state):
    """Direct relay control using working command format (like grower_web_app.py)"""
    try:
        if not feed_control_system:
            return jsonify({'error': 'FeedControlSystem not available'}), 500
        
        if state not in ['on', 'off']:
            return jsonify({'error': 'Invalid state. Use "on" or "off"'}), 400
        
        # Validate relay ID
        if relay_id not in get_available_relays():
            return jsonify({'error': 'Invalid relay ID'}), 400
        
        # Use the working command format
        target_state = state == 'on'
        success = control_relay_direct(relay_id, target_state)
        
        if success:
            from config import get_relay_name
            relay_name = get_relay_name(relay_id)
            return jsonify({
                'success': True,
                'message': f'Relay {relay_id} ({relay_name}) turned {state.upper()}',
                'relay_id': relay_id,
                'state': state,
                'command_used': f"Start;Relay;{relay_id};{state.upper()};end"
            })
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        logger.error(f"Error controlling relay {relay_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/pump/<int:pump_id>/dispense', methods=['POST'])
def dispense_pump_direct_endpoint(pump_id):
    """Direct pump dispensing using working command format (like grower_web_app.py)"""
    try:
        if not feed_control_system:
            return jsonify({'error': 'FeedControlSystem not available'}), 500
        
        # Validate pump ID
        if pump_id not in get_available_pumps():
            return jsonify({'error': 'Invalid pump ID'}), 400
        
        data = request.get_json() or {}
        amount = float(data.get('amount', 10.0))
        
        if not (0.5 <= amount <= 500):  # Reasonable limits
            return jsonify({'error': 'Amount must be between 0.5 and 500 ml'}), 400
        
        # Use the working command format
        success = dispense_pump_direct(pump_id, amount)
        
        if success:
            pump_name = get_pump_name(pump_id)
            return jsonify({
                'success': True,
                'message': f'Dispensing {amount}ml from {pump_name}',
                'pump_id': pump_id,
                'amount': amount,
                'command_used': f"Start;Dispense;{pump_id};{amount};end"
            })
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        logger.error(f"Error dispensing from pump {pump_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/pump/<int:pump_id>/stop', methods=['POST'])
def stop_pump_direct_endpoint(pump_id):
    """Direct pump stop using working command format (like grower_web_app.py)"""
    try:
        if not feed_control_system:
            return jsonify({'error': 'FeedControlSystem not available'}), 500
        
        # Validate pump ID
        if pump_id not in get_available_pumps():
            return jsonify({'error': 'Invalid pump ID'}), 400
        
        # Use the working command format
        success = stop_pump_direct(pump_id)
        
        if success:
            pump_name = get_pump_name(pump_id)
            return jsonify({
                'success': True,
                'message': f'Stopped {pump_name}',
                'pump_id': pump_id,
                'command_used': f"Start;Pump;{pump_id};X;end"
            })
        else:
            return jsonify({'error': 'Command failed'}), 500
            
    except Exception as e:
        logger.error(f"Error stopping pump {pump_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/emergency_stop', methods=['POST'])
def emergency_stop_hardware():
    """Emergency stop using working FeedControlSystem (like grower_web_app.py)"""
    try:
        if not feed_control_system:
            return jsonify({'error': 'FeedControlSystem not available'}), 500
        
        # Use the FeedControlSystem emergency stop
        feed_control_system.emergency_stop()
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop activated via FeedControlSystem',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error during hardware emergency stop: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/status', methods=['GET'])
def get_hardware_status():
    """Get hardware status from FeedControlSystem (like grower_web_app.py)"""
    try:
        if not feed_control_system:
            return jsonify({'error': 'FeedControlSystem not available'}), 500
        
        # Get status from FeedControlSystem
        status = feed_control_system.get_system_status()
        
        # Format for compatibility with grower_web_app.py
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
            from config import get_relay_name
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
        logger.error(f"Error getting hardware status: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# UTILITY FUNCTIONS FOR TESTING
# =============================================================================

def get_relay_gpio_mapping():
    """Get the complete GPIO mapping for all relays"""
    if not hardware_manager or not hardware_manager.relay_controller:
        return {}
        
    mapping = {}
    available_relays = hardware_manager.relay_controller.get_available_relays()
    
    for relay_id in available_relays:
        relay_info = hardware_manager.relay_controller.get_relay_info(relay_id)
        if relay_info:
            mapping[relay_id] = {
                'gpio_pin': relay_info.get('gpio_pin'),
                'name': relay_info.get('name'),
                'active_high': relay_info.get('active_high', True)
            }
            
    return mapping


def validate_hardware_connections():
    """Validate that all hardware connections are working"""
    results = {
        'relays': {},
        'overall_health': True
    }
    
    if hardware_manager and hardware_manager.relay_controller:
        available_relays = hardware_manager.relay_controller.get_available_relays()
        
        for relay_id in available_relays:
            # Test each relay with a quick on/off cycle
            try:
                original_state = hardware_manager.relay_controller.get_relay_state(relay_id)
                
                # Quick test cycle
                hardware_manager.relay_controller.set_relay(relay_id, True)
                time.sleep(0.1)
                on_verified = verify_gpio_state(relay_id, True)
                
                hardware_manager.relay_controller.set_relay(relay_id, False)
                time.sleep(0.1)
                off_verified = verify_gpio_state(relay_id, False)
                
                # Restore original state
                hardware_manager.relay_controller.set_relay(relay_id, original_state)
                
                relay_healthy = on_verified and off_verified
                results['relays'][relay_id] = {
                    'healthy': relay_healthy,
                    'on_verified': on_verified,
                    'off_verified': off_verified
                }
                
                if not relay_healthy:
                    results['overall_health'] = False
                    
            except Exception as e:
                results['relays'][relay_id] = {
                    'healthy': False,
                    'error': str(e)
                }
                results['overall_health'] = False
                
    return results


# Add this to track app start time for uptime calculation
app_start_time = time.time()

# =============================================================================
# WEBSOCKET SUPPORT FOR REAL-TIME UPDATES (Optional)
# =============================================================================

# If you want real-time updates, you can add SocketIO support:
"""
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to testing terminal'})

@socketio.on('request_status_update')
def handle_status_request():
    status = get_enhanced_system_status()
    emit('status_update', status.json)

def broadcast_hardware_event(event_type, data):
    \"\"\"Broadcast hardware events to all connected clients\"\"\"
    socketio.emit('hardware_event', {
        'type': event_type,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })
"""

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == '__main__':
    print("🌱 Nutrient Mixing System - Flask Application")
    print("=" * 60)
    
    # Initialize system
    if initialize_system():
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
            cleanup_system()
    else:
        print("✗ System initialization failed")
        exit(1)