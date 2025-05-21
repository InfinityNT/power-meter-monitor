"""
Power Meter Monitoring System

A complete system for monitoring power meters via USB connection,
collecting real-time data, and providing that data through an HTTP API.

Main components:
- Power meter communication (reader)
- Data collection and management
- HTTP API for accessing meter data
- Testing tools including a simulator
"""

# Version and metadata
__version__ = '0.1.0'
__author__ = 'Eduardo Murillo'
__email__ = 'eduardo.murillo@ttelectronics.com'
__license__ = 'MIT'

# Import key components for easy access
from powermeter import PowerMeterReader, PowerMeterDataManager, PowerMeterHTTPServer
from config import CONFIG
from tests import PowerMeterSimulator

# Define package exports
__all__ = [
    'PowerMeterReader', 
    'PowerMeterDataManager', 
    'PowerMeterHTTPServer',
    'CONFIG',
    'PowerMeterSimulator'
]

# Package initialization code (if needed)
import os
import logging

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)