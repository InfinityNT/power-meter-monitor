"""
Modbus protocol implementation package for power meter communication
"""

__version__ = '0.1.0'

# Import key components for easier access
from .protocol import calculate_crc, build_command, parse_response, get_expected_response_length
from .client import ModbusClient
from .registers import REGISTERS, REGISTER_GROUPS, get_register_name, get_register_group

# Define package exports
__all__ = [
    'calculate_crc', 
    'build_command', 
    'parse_response', 
    'get_expected_response_length',
    'ModbusClient',
    'REGISTERS', 
    'REGISTER_GROUPS', 
    'get_register_name', 
    'get_register_group'
]