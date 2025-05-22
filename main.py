import signal
import sys
import time
import logging
import os

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config import CONFIG
from core import PowerMeterReader, PowerMeterDataManager, AuthenticationManager
from api import PowerMeterHTTPServer
from web.static_server import start_test_server

logger = logging.getLogger('powermeter.main')

# Flag to control application running state
running = True

def signal_handler(sig, frame):
    logger.info("Shutdown signal received")
    global running
    running = False

def main():
    logger.info("Starting power meter monitoring application")
    
    # Create authentication manager
    auth_manager = AuthenticationManager()
    logger.info(f"Authentication system initialized with users: {list(auth_manager.users.keys())}")
    
    # Create reader with configuration from settings
    reader = PowerMeterReader(
        CONFIG['SERIAL_PORT'],
        CONFIG['BAUD_RATE'],
        CONFIG['TIMEOUT']
    )
    
    # Set additional reader properties from config
    reader.device_address = CONFIG.get('MODBUS_ADDRESS', 1)
    
    # Test connection
    logger.info("Testing connection to power meter...")
    if not reader.test_connection():
        logger.error("Failed to communicate with power meter. Please check:")
        logger.error(f"1. Is the power meter connected via USB to {CONFIG['SERIAL_PORT']}?")
        logger.error(f"2. Is the baud rate set correctly ({CONFIG['BAUD_RATE']})?")
        logger.error("3. Are other communication parameters correct (data bits, parity, etc.)?")
        logger.error("Exiting.")
        return 1
    
    logger.info("Power meter connection test successful!")
    
    # Create custom data manager that uses the detailed data function if configured
    class CustomPowerMeterDataManager(PowerMeterDataManager):
        def _read_meter_loop(self):
            """Continuously read from the meter"""
            while self.running:
                try:
                    # Use detailed data if configured, otherwise use regular data
                    if CONFIG.get('DETAILED_DATA', False):
                        data = self.reader.read_detailed_data()
                    else:
                        data = self.reader.read_basic_data()
                        
                    if data is not None:
                        self.meter_data = data
                        logger.info(f"Updated readings: Power={data.get('system', {}).get('power_kw', data.get('power_kw', 'N/A'))}kW")
                except Exception as e:
                    logger.error(f"Error in meter reading loop: {str(e)}")
                time.sleep(self.poll_interval)
    
    # Create data manager
    data_manager = CustomPowerMeterDataManager(reader, CONFIG['POLL_INTERVAL'])
    
    # Create HTTP server
    http_server = PowerMeterHTTPServer(CONFIG['HTTP_PORT'], data_manager)
    
    try:
        # Start the web interface
        web_port = CONFIG.get('WEB_PORT', 8000)
        start_test_server(web_port)
        logger.info(f"Web interface available at http://localhost:{web_port}/login.html")
        logger.info("Authentication enabled - use login page to access monitor")
        
        # Start components
        data_manager.start()
        http_server.start()
        
        logger.info(f"System running. HTTP API available at http://localhost:{CONFIG['HTTP_PORT']}/")
        logger.info("Default users: admin/admin, operator/operator, viewer/viewer")
        logger.info("Press Ctrl+C to exit.")
        
        # Keep main thread alive
        global running
        while running:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1
    finally:
        # Clean shutdown
        http_server.stop()
        data_manager.stop()
        reader.disconnect()
        logger.info("Application shut down")
    
    return 0

if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the main function
    sys.exit(main())