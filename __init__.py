"""
Power Monitor System

A complete system for monitoring power meters via USB connection,
collecting real-time data, and providing that data through an HTTP API.

Main components:
- Power meter communication (reader)
- Data collection and management
- HTTP API for accessing meter data
- Authentication and user management
- Testing tools including a simulator
"""

# Version and metadata
__version__ = '0.1.0'
__author__ = 'Eduardo Murillo'
__email__ = 'eduardo.murillo@ttelectronics.com'
__license__ = 'MIT'

# Import key components for easy access (using relative imports)
from core import (
    PowerMeterReader, 
    PowerMeterDataManager, 
    PowerMeterSimulator,
    AuthenticationManager,
    User,
    Session
)

from api import (
    PowerMeterHTTPServer,
    PowerMeterHTTPHandler
)

from config import CONFIG

# Define package exports
__all__ = [
    'PowerMeterReader', 
    'PowerMeterDataManager', 
    'PowerMeterHTTPServer',
    'PowerMeterHTTPHandler',
    'AuthenticationManager',
    'User',
    'Session',
    'CONFIG',
    'PowerMeterSimulator'
]

# Package initialization code
import os
import logging

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)