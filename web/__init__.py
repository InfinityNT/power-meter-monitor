"""
Web interface package for power meter monitoring system
"""

__version__ = '0.1.0'

# Import static server for easier access
from .static_server import serve_static_files, start_static_server

# Define package exports
__all__ = ['serve_static_files', 'start_static_server']