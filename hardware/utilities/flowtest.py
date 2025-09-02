#!/usr/bin/env python3
"""
Quick Flow Meter Pulse Test Script
Run this while water is flowing to verify pulse counting

Usage:
  python test_flow_pulses.py [meter_id]
  
Example:
  python test_flow_pulses.py 1    # Test meter 1 (Tank Fill)
  python test_flow_pulses.py 2    # Test meter 2 (Tank Send)
"""

import sys
import time
import signal
import logging
from datetime import datetime

# Import your flow meter controller
try:
    from hardware.rpi_flow import FlowMeterController
    from config import get_flow_meter_name, get_available_flow_meters
    MOCK_MODE = False
except ImportError as e:
    print(f"Import error: {e}")
    print("Using mock mode for testing...")
    from hardware.rpi_flow import MockFlowMeterController as FlowMeterController
    from config import get_flow_meter_name, get_available_flow_meters
    MOCK_MODE = True

# Global variables
controller = None
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running, controller
    print("\n\n🛑 Stopping test...")
    running = False
    if controller:
        controller.cleanup()
    sys.exit(0)

def calculate_flow_rate(pulse_count, time_elapsed, pulses_per_gallon):
    """Calculate flow rate in gallons per minute"""
    if time_elapsed <= 0:
        return 0.0
    
    gallons = pulse_count / pulses_per_gallon
    gallons_per_minute = (gallons / time_elapsed) * 60
    return gallons_per_minute

def print_header(meter_id, meter_name, gpio_pin):
    """Print test header"""
    print("=" * 70)
    print(f"🌊 FLOW METER PULSE TEST")
    print(f"   Meter: {meter_id} - {meter_name}")
    print(f"   GPIO Pin: {gpio_pin}")
    print(f"   Mode: {'MOCK' if MOCK_MODE else 'REAL HARDWARE'}")
    print("=" * 70)
    print("💡 Turn on water flow and watch for pulse counts!")
    print("   Press Ctrl+C to stop")
    print()
    print(f"{'Time':<12} {'Pulses':<8} {'Rate':<10} {'Gallons':<10} {'GPM':<8}")
    print("-" * 60)

def main():
    global controller, running
    
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Get meter ID from command line or use default
    if len(sys.argv) > 1:
        try:
            meter_id = int(sys.argv[1])
        except ValueError:
            print("❌ Error: meter_id must be a number (1 or 2)")
            sys.exit(1)
    else:
        available_meters = get_available_flow_meters()
        if not available_meters:
            print("❌ Error: No flow meters configured")
            sys.exit(1)
        meter_id = available_meters[0]  # Use first available
        print(f"ℹ️  Using default meter: {meter_id}")
    
    # Validate meter
    available_meters = get_available_flow_meters()
    if meter_id not in available_meters:
        print(f"❌ Error: Invalid meter ID {meter_id}")
        print(f"   Available meters: {available_meters}")
        sys.exit(1)
    
    try:
        # Initialize controller
        print("🔧 Initializing flow meter controller...")
        controller = FlowMeterController()
        
        # Get meter info
        meter_name = get_flow_meter_name(meter_id)
        status = controller.get_flow_status(meter_id)
        gpio_pin = status.get('name', 'Unknown') if status else 'Unknown'
        
        # Print header
        print_header(meter_id, meter_name, gpio_pin)
        
        # Start monitoring (don't set target - just count pulses)
        controller.flow_meters[meter_id]['status'] = 1  # Activate for monitoring
        controller.flow_meters[meter_id]['pulse_count'] = 0  # Reset counter
        
        # Get initial values
        start_time = time.time()
        last_pulse_count = 0
        last_time = start_time
        
        # Main monitoring loop
        while running:
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # Get current status
            status = controller.get_flow_status(meter_id)
            if not status:
                print("❌ Error: Could not get meter status")
                break
                
            pulse_count = status['pulse_count']
            pulses_per_gallon = status['pulses_per_gallon']
            
            # Calculate metrics
            total_gallons = pulse_count / pulses_per_gallon
            current_gpm = calculate_flow_rate(pulse_count, elapsed_time, pulses_per_gallon)
            
            # Calculate instantaneous rate (pulses in last second)
            time_since_last = current_time - last_time
            if time_since_last >= 1.0:  # Update every second
                pulses_this_period = pulse_count - last_pulse_count
                instant_gpm = calculate_flow_rate(pulses_this_period, time_since_last, pulses_per_gallon)
                
                # Format time
                time_str = f"{elapsed_time:8.1f}s"
                
                # Print current status
                print(f"{time_str:<12} {pulse_count:<8} {pulses_this_period:<10} {total_gallons:<10.3f} {instant_gpm:<8.2f}")
                
                # Update for next iteration
                last_pulse_count = pulse_count
                last_time = current_time
            
            time.sleep(0.1)  # Small delay to prevent CPU hammering
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        if controller:
            controller.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()