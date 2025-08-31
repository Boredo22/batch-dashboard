#!/usr/bin/env python3
"""
Mock implementations of smbus2 and lgpio libraries for Windows development
These mocks allow the application to run on systems without the actual hardware libraries
"""

import time
import logging

logger = logging.getLogger(__name__)

class MockSMBus:
    """Mock implementation of smbus2.SMBus for I2C communication"""
    
    def __init__(self, bus_number):
        self.bus_number = bus_number
        logger.info(f"Mock SMBus initialized for bus {bus_number}")
    
    def write_i2c_block_data(self, address, register, data):
        """Mock I2C block write"""
        logger.debug(f"Mock I2C write to address {address:#04x}, register {register}, data: {data}")
        return True
    
    def read_i2c_block_data(self, address, register, length):
        """Mock I2C block read - returns mock response"""
        logger.debug(f"Mock I2C read from address {address:#04x}, register {register}, length {length}")
        # Return mock "success" response for EZO pumps
        return [1, 0, 0, 0]  # EZO_RESPONSE_CODES['success'] format
    
    def close(self):
        """Mock close connection"""
        logger.debug("Mock SMBus closed")

class MockLGPIO:
    """Mock implementation of lgpio library for GPIO operations"""
    
    # Mock GPIO constants
    INPUT = 0
    OUTPUT = 1
    SET_PULL_UP = 1
    SET_PULL_DOWN = 2
    BOTH_EDGES = 3
    RISING_EDGE = 1
    FALLING_EDGE = 2
    
    @staticmethod
    def gpiochip_open(chip):
        """Mock GPIO chip open - returns mock handle"""
        logger.info(f"Mock GPIO chip {chip} opened")
        return 1  # Mock handle
    
    @staticmethod
    def gpiochip_close(handle):
        """Mock GPIO chip close"""
        logger.debug(f"Mock GPIO chip closed (handle {handle})")
        return 0
    
    @staticmethod
    def gpio_claim_output(handle, pin, level=0):
        """Mock GPIO claim as output"""
        logger.debug(f"Mock GPIO pin {pin} claimed as output (level {level})")
        return 0
    
    @staticmethod
    def gpio_claim_input(handle, pin, flags=0):
        """Mock GPIO claim as input"""
        logger.debug(f"Mock GPIO pin {pin} claimed as input (flags {flags})")
        return 0
    
    @staticmethod
    def gpio_write(handle, pin, level):
        """Mock GPIO write"""
        logger.debug(f"Mock GPIO write pin {pin} level {level}")
        return 0
    
    @staticmethod
    def gpio_read(handle, pin):
        """Mock GPIO read"""
        logger.debug(f"Mock GPIO read pin {pin}")
        return 0  # Always return low
    
    @staticmethod
    def gpio_free(handle, pin):
        """Mock GPIO free"""
        logger.debug(f"Mock GPIO pin {pin} freed")
        return 0
    
    @staticmethod
    def callback(handle, pin, edge, func):
        """Mock GPIO callback setup"""
        logger.debug(f"Mock GPIO callback set for pin {pin} on edge {edge}")
        return 1  # Mock callback ID
    
    @staticmethod
    def callback_cancel(callback_id):
        """Mock GPIO callback cancel"""
        logger.debug(f"Mock GPIO callback {callback_id} cancelled")
        return 0

# Create mock modules that can be imported
class MockSMBus2Module:
    SMBus = MockSMBus

class MockLGPIOModule:
    def __getattr__(self, name):
        return getattr(MockLGPIO, name)

# Instances that will be used as mock modules
smbus2 = MockSMBus2Module()
lgpio = MockLGPIOModule()