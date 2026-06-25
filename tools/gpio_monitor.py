#!/usr/bin/env python3
"""
GPIO Monitor - Like a Digital Multimeter for GPIO Pins
Continuously monitors GPIO levels to help debug optocoupler connections
"""

import time
import signal
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import lgpio
    MOCK_MODE = False
except ImportError:
    print("⚠️  lgpio not available - using mock mode")
    from hardware.mock_hardware_libs import lgpio
    MOCK_MODE = True

from config import FLOW_METER_GPIO_PINS, FLOW_METER_NAMES

# Global variables
h = None
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running, h
    print("\n🛑 Stopping GPIO monitor...")
    running = False
    cleanup_gpio()
    sys.exit(0)

def cleanup_gpio():
    """Clean up GPIO resources"""
    global h
    if h is not None:
        try:
            lgpio.gpiochip_close(h)
            h = None
            print("✓ GPIO cleanup completed")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

def read_gpio_level(gpio_pin):
    """Read current GPIO level"""
    global h
    
    if h is None:
        return None
        
    try:
        return lgpio.gpio_read(h, gpio_pin)
    except Exception as e:
        return None

def main():
    global h, running
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print("📊 GPIO LEVEL MONITOR")
    print(f"   Mode: {'MOCK HARDWARE' if MOCK_MODE else 'REAL HARDWARE'}")
    print("=" * 70)
    
    if MOCK_MODE:
        print("⚠️  Running in mock mode - no real GPIO monitoring possible")
        print("   Install lgpio with: pip install lgpio")
        return
    
    try:
        # Initialize GPIO
        print("🔧 Initializing GPIO...")
        h = lgpio.gpiochip_open(0)
        print("✓ GPIO chip opened")
        
        # Setup GPIO pins as inputs
        gpio_pins = []
        for meter_id, gpio_pin in FLOW_METER_GPIO_PINS.items():
            try:
                lgpio.gpio_claim_input(h, gpio_pin, lgpio.SET_PULL_UP)
                gpio_pins.append((meter_id, gpio_pin))
                print(f"✓ GPIO {gpio_pin} configured for {FLOW_METER_NAMES.get(meter_id, f'Meter {meter_id}')}")
            except Exception as e:
                print(f"❌ Error setting up GPIO {gpio_pin}: {e}")
        
        if not gpio_pins:
            print("❌ No GPIO pins configured!")
            return
        
        print("\n" + "=" * 70)
        print("💡 MONITORING GPIO LEVELS (Updates every 0.1 seconds)")
        print("   HIGH = 3.3V (no flow or optocoupler off)")
        print("   LOW  = 0V   (pulse detected or optocoupler on)")
        print("   Press Ctrl+C to stop")
        print("=" * 70)
        print()
        
        # Print header
        header = "Time     "
        for meter_id, gpio_pin in gpio_pins:
            meter_name = FLOW_METER_NAMES.get(meter_id, f"M{meter_id}")[:8]  # Truncate to 8 chars
            header += f"{meter_name:>8s} "
        print(header)
        print("-" * len(header))
        
        # Track level changes
        last_levels = {}
        change_counts = {}
        
        # Initialize tracking
        for meter_id, gpio_pin in gpio_pins:
            last_levels[meter_id] = None
            change_counts[meter_id] = 0
        
        # Main monitoring loop
        while running:
            timestamp = time.strftime('%H:%M:%S')
            status_line = f"{timestamp} "
            
            level_changed = False
            
            for meter_id, gpio_pin in gpio_pins:
                level = read_gpio_level(gpio_pin)
                
                if level is not None:
                    level_str = "HIGH" if level else "LOW "
                    
                    # Check for level changes
                    if last_levels[meter_id] is not None and last_levels[meter_id] != level:
                        change_counts[meter_id] += 1
                        level_changed = True
                        level_str += "*"  # Mark changes
                    else:
                        level_str += " "
                    
                    last_levels[meter_id] = level
                    
                else:
                    level_str = "ERROR"
                
                status_line += f"{level_str:>8s} "
            
            # Print line (only print every change or every 10 seconds)
            if level_changed or (int(time.time()) % 10 == 0):
                print(status_line)
                
                # Print change summary if there were changes
                if level_changed:
                    change_summary = "         "  # Align with timestamp
                    for meter_id, gpio_pin in gpio_pins:
                        changes = change_counts[meter_id]
                        change_summary += f"({changes:3d}ch)  "
                    print(change_summary)
            
            time.sleep(0.1)  # 100ms update rate
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Monitor failed: {e}")
        cleanup_gpio()
        sys.exit(1)

if __name__ == "__main__":
    main()