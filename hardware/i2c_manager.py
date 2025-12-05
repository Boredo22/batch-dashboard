#!/usr/bin/env python3
"""
Shared I2C Bus Manager
Single bus instance for all I2C devices (pumps at 11-18, pH at 0x63, EC at 0x64)
"""

import threading
import smbus2
import logging
import time

logger = logging.getLogger(__name__)

class I2CManager:
    """Thread-safe singleton for I2C bus access"""
    _instance = None
    _lock = threading.Lock()
    _bus_lock = threading.Lock()

    def __new__(cls, bus_number=1):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._bus = None
                    cls._instance._bus_number = bus_number
                    cls._instance._initialize_bus()
        return cls._instance

    def _initialize_bus(self):
        """Initialize the I2C bus"""
        try:
            self._bus = smbus2.SMBus(self._bus_number)
            logger.info(f"I2C bus {self._bus_number} initialized")
        except Exception as e:
            logger.error(f"Failed to initialize I2C bus: {e}")
            self._bus = None

    @property
    def bus(self):
        """Get the bus instance"""
        return self._bus

    def send_command(self, address, command, delay=0.3):
        """
        Send command to EZO device with proper locking
        Returns: (success, response_code, data_string)
        """
        if self._bus is None:
            return False, 0, "Bus not initialized"

        with self._bus_lock:
            try:
                # Use raw I2C messages (required for EZO devices)
                write_msg = smbus2.i2c_msg.write(address, list(command.encode('utf-8')))
                self._bus.i2c_rdwr(write_msg)

                # Wait for processing
                time.sleep(delay)

                # Read response
                read_msg = smbus2.i2c_msg.read(address, 32)
                self._bus.i2c_rdwr(read_msg)

                data = list(read_msg)
                response_code = data[0]

                if response_code == 1:  # Success
                    response_str = ''.join([chr(x) for x in data[1:] if 32 <= x <= 126]).strip()
                    return True, response_code, response_str
                else:
                    return False, response_code, ""

            except Exception as e:
                logger.error(f"I2C error at address {address}: {e}")
                return False, 0, str(e)

    def close(self):
        """Close the I2C bus"""
        with self._bus_lock:
            if self._bus:
                self._bus.close()
                self._bus = None


def get_i2c_manager():
    """Get the shared I2C manager instance"""
    return I2CManager()
