"""
Core functionality package for power meter data management
"""

__version__ = '0.1.0'

# Import key components for easier access
from .data_manager import PowerMeterDataManager
from .reader import PowerMeterReader
from .simulator import PowerMeterSimulator

# Import authentication components
from .auth import User, Session, AuthenticationManager

# Define package exports
__all__ = [
    'PowerMeterDataManager', 
    'PowerMeterReader', 
    'PowerMeterSimulator',
    'User',
    'Session', 
    'AuthenticationManager'
]