"""
Flask Hardware Control System - Restart and Resource Conflict Fixes
==================================================================

This module provides fixes for:
1. Flask debug mode auto-restarts
2. GPIO resource conflicts 
3. I2C bus race conditions
4. Multiple instance prevention
5. Proper cleanup on shutdown
"""

import os
import sys
import time
import atexit
import signal
import threading
import logging
from contextlib import contextmanager
from typing import Optional, Any

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for development/testing
    class MockGPIO:
        def cleanup(self): pass
        def setup(self, pin, mode): pass
        def setmode(self, mode): pass
        OUT = 1
        BCM = 1
    GPIO = MockGPIO()

logger = logging.getLogger(__name__)

# =============================================================================
# 1. INSTANCE LOCK MANAGER
# =============================================================================

class InstanceLockManager:
    """Prevents multiple instances from running simultaneously"""
    
    def __init__(self, lock_file_path: str = '/tmp/feed_control.lock'):
        self.lock_file = lock_file_path
        self.pid = os.getpid()
    
    def acquire_lock(self) -> bool:
        """Acquire instance lock, return True if successful"""
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if old process is still running
                try:
                    os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                    print(f"Another instance (PID {old_pid}) is already running. Exiting...")
                    return False
                except OSError:
                    # Process doesn't exist, remove stale lock file
                    print(f"Removing stale lock file (PID {old_pid} not running)")
                    os.remove(self.lock_file)
            except (ValueError, FileNotFoundError):
                # Invalid lock file, remove it
                print("Removing invalid lock file")
                try:
                    os.remove(self.lock_file)
                except FileNotFoundError:
                    pass
        
        # Create new lock file
        try:
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
            print(f"Instance lock acquired (PID {self.pid})")
            return True
        except Exception as e:
            print(f"Failed to create lock file: {e}")
            return False
    
    def release_lock(self):
        """Release instance lock"""
        try:
            if os.path.exists(self.lock_file):
                with open(self.lock_file, 'r') as f:
                    lock_pid = int(f.read().strip())
                
                if lock_pid == self.pid:
                    os.remove(self.lock_file)
                    print(f"Instance lock released (PID {self.pid})")
        except Exception as e:
            print(f"Error releasing lock: {e}")

# =============================================================================
# 2. GPIO RESOURCE MANAGER
# =============================================================================

class GPIOResourceManager:
    """Manages GPIO resources and prevents conflicts"""
    
    def __init__(self):
        self._initialized = False
        self._used_pins = set()
    
    def is_gpio_in_use(self, pin: int) -> bool:
        """Check if GPIO pin is already in use"""
        try:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.cleanup(pin)
            return False
        except Exception as e:
            logger.warning(f"GPIO pin {pin} appears to be in use: {e}")
            return True
    
    def safe_gpio_setup(self, pin: int, mode, retries: int = 3) -> bool:
        """Safely setup GPIO with retries"""
        for attempt in range(retries):
            try:
                if not self.is_gpio_in_use(pin):
                    GPIO.setup(pin, mode)
                    self._used_pins.add(pin)
                    return True
                else:
                    print(f"GPIO pin {pin} is busy, waiting... (attempt {attempt + 1})")
                    time.sleep(1)
            except Exception as e:
                logger.error(f"GPIO setup failed for pin {pin}: {e}")
                time.sleep(1)
        
        logger.error(f"Failed to setup GPIO pin {pin} after {retries} attempts")
        return False
    
    def cleanup_gpio(self):
        """Clean up all GPIO resources"""
        try:
            GPIO.cleanup()
            self._used_pins.clear()
            logger.info("GPIO cleaned up successfully")
        except Exception as e:
            logger.error(f"GPIO cleanup error: {e}")

# =============================================================================
# 3. I2C BUS MANAGER
# =============================================================================

class I2CBusManager:
    """Thread-safe singleton I2C bus manager"""
    
    _instance: Optional['I2CBusManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'I2CBusManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._i2c_lock = threading.Lock()
            self._bus = None
            self._bus_number = 1
            self._initialized = True
    
    @contextmanager
    def get_bus(self, bus_number: int = 1):
        """Get I2C bus with thread-safe locking"""
        with self._i2c_lock:
            try:
                if self._bus is None or self._bus_number != bus_number:
                    # Import here to avoid issues if not available
                    try:
                        import board
                        import busio
                        self._bus = busio.I2C(board.SCL, board.SDA)
                        self._bus_number = bus_number
                        logger.info(f"I2C bus {bus_number} initialized")
                    except ImportError:
                        logger.warning("I2C libraries not available, using mock")
                        self._bus = MockI2CBus()
                
                yield self._bus
            except Exception as e:
                logger.error(f"I2C bus error: {e}")
                self._bus = None
                raise
    
    def close_bus(self):
        """Close I2C bus connection"""
        with self._i2c_lock:
            if self._bus:
                try:
                    if hasattr(self._bus, 'deinit'):
                        self._bus.deinit()
                    logger.info("I2C bus closed")
                except Exception as e:
                    logger.error(f"Error closing I2C bus: {e}")
                finally:
                    self._bus = None

class MockI2CBus:
    """Mock I2C bus for testing/development"""
    def deinit(self): pass

# =============================================================================
# 4. HARDWARE SAFETY MANAGER
# =============================================================================

class HardwareSafetyManager:
    """Main hardware safety and resource management"""
    
    def __init__(self):
        self.lock_manager = InstanceLockManager()
        self.gpio_manager = GPIOResourceManager()
        self.i2c_manager = I2CBusManager()
        self._shutdown_handlers_registered = False
    
    def setup_safety_systems(self) -> bool:
        """Setup all safety systems"""
        print("Setting up hardware safety systems...")
        
        # 1. Check for existing instance
        if not self.lock_manager.acquire_lock():
            return False
        
        # 2. Register shutdown handlers
        self._register_shutdown_handlers()
        
        # 3. Setup GPIO mode
        try:
            GPIO.setmode(GPIO.BCM)
            logger.info("GPIO mode set to BCM")
        except Exception as e:
            logger.error(f"Failed to set GPIO mode: {e}")
        
        print("Hardware safety systems initialized successfully")
        return True
    
    def _register_shutdown_handlers(self):
        """Register cleanup handlers for various shutdown scenarios"""
        if self._shutdown_handlers_registered:
            return
        
        def cleanup_handler():
            """Main cleanup handler"""
            print("Performing hardware cleanup...")
            self.gpio_manager.cleanup_gpio()
            self.i2c_manager.close_bus()
            self.lock_manager.release_lock()
        
        def signal_handler(signum, frame):
            """Handle shutdown signals"""
            print(f"Received signal {signum}, shutting down gracefully...")
            cleanup_handler()
            sys.exit(0)
        
        # Register handlers
        atexit.register(cleanup_handler)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self._shutdown_handlers_registered = True
        logger.info("Shutdown handlers registered")
    
    def safe_hardware_init(self, init_function, max_retries: int = 3):
        """Safely initialize hardware with retries"""
        for attempt in range(max_retries):
            try:
                print(f"Hardware initialization attempt {attempt + 1}/{max_retries}")
                result = init_function()
                print("Hardware initialization successful")
                return result
            except Exception as e:
                logger.error(f"Hardware init attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print("Hardware initialization failed after all retries")
                    raise
    
    def emergency_stop(self):
        """Emergency stop all hardware"""
        print("EMERGENCY STOP INITIATED")
        try:
            # Add your emergency stop logic here
            self.gpio_manager.cleanup_gpio()
            self.i2c_manager.close_bus()
            logger.warning("Emergency stop completed")
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")

# =============================================================================
# 5. FLASK APP CONFIGURATION FIXES
# =============================================================================

def configure_flask_for_hardware(app):
    """Configure Flask app for hardware control"""
    
    # Disable debug mode in production
    app.config['DEBUG'] = False
    
    # Disable auto-reload to prevent hardware conflicts
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    
    # Set other safe defaults
    app.config['TESTING'] = False
    
    print("Flask configured for hardware control (debug=False)")

# =============================================================================
# 6. MAIN SETUP FUNCTION
# =============================================================================

def setup_hardware_safety(app=None) -> HardwareSafetyManager:
    """
    Main function to setup all hardware safety systems
    
    Usage:
        safety_manager = setup_hardware_safety(app)
        if not safety_manager:
            sys.exit(1)
    """
    
    safety_manager = HardwareSafetyManager()
    
    # Setup safety systems
    if not safety_manager.setup_safety_systems():
        print("Failed to setup safety systems - another instance may be running")
        return None
    
    # Configure Flask if provided
    if app:
        configure_flask_for_hardware(app)
    
    return safety_manager