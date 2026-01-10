#!/usr/bin/env python3
"""
Shared I2C Bus Manager
Single bus instance for all I2C devices (pumps at 11-18, pH at 0x63, EC at 0x64)
Includes timeout protection to prevent indefinite blocking on I2C operations.
"""

import threading
import concurrent.futures
import smbus2
import logging
import time

from config import I2C_OPERATION_TIMEOUT

logger = logging.getLogger(__name__)

class I2CManager:
    """Thread-safe singleton for I2C bus access with timeout protection"""
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
                    # Use multiple workers so a stuck operation doesn't block everything
                    cls._instance._executor = concurrent.futures.ThreadPoolExecutor(
                        max_workers=4, thread_name_prefix="i2c"
                    )
                    cls._instance._pending_futures = []
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

    def _send_command_internal(self, address, command, delay):
        """
        Internal method to send command - called within timeout wrapper.
        Returns: (success, response_code, data_string)
        """
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

    def _cleanup_stale_futures(self):
        """Clean up completed futures from tracking list."""
        self._pending_futures = [
            f for f in self._pending_futures
            if not f.done()
        ]

    def send_command(self, address, command, delay=0.3, timeout=None):
        """
        Send command to EZO device with timeout protection.

        Args:
            address: I2C address of the device
            command: Command string to send
            delay: Delay in seconds after sending command (default 0.3s for EZO devices)
            timeout: Timeout in seconds (defaults to I2C_OPERATION_TIMEOUT)

        Returns: (success, response_code, data_string)
        """
        if self._bus is None:
            return False, 0, "Bus not initialized"

        if timeout is None:
            timeout = I2C_OPERATION_TIMEOUT

        # Clean up old completed futures
        self._cleanup_stale_futures()

        # Submit the I2C operation to the executor with timeout
        future = self._executor.submit(self._send_command_internal, address, command, delay)
        self._pending_futures.append(future)

        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.error(f"I2C operation timed out after {timeout}s for address {address} command '{command}'")
            # Try to cancel (won't work if running, but good practice)
            future.cancel()
            # Return a timeout error - the bus may be stuck
            return False, 0, f"I2C timeout after {timeout}s"

    def close(self):
        """Close the I2C bus and shutdown executor"""
        with self._bus_lock:
            if self._bus:
                self._bus.close()
                self._bus = None

        # Shutdown the executor
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


def get_i2c_manager():
    """Get the shared I2C manager instance"""
    return I2CManager()
