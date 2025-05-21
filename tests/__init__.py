"""
Tests package for power meter monitoring system
"""

__version__ = '0.1.0'

# Import components from their actual locations
from core.simulator import PowerMeterSimulator
from web.static_server import start_static_server as start_test_server

# Define package exports
__all__ = ['PowerMeterSimulator', 'start_test_server']