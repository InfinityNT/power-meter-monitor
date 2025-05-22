import signal
import sys
import time
import logging
import os

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config import CONFIG
from core import PowerMeterDataManager, AuthenticationManager
from core.simulator import PowerMeterSimulator
from api import PowerMeterHTTPServer
from web.static_server import start_static_server

logger = logging.getLogger('powermeter.test')

def main():
    logger.info("Starting power meter test application with simulator")
    
    # Create authentication manager
    auth_manager = AuthenticationManager()
    logger.info(f"Authentication system initialized with users: {list(auth_manager.users.keys())}")
    
    # Create simulated reader instead of real hardware
    reader = PowerMeterSimulator()
    
    # Create custom data manager that maintains the simulator's interface
    class CustomPowerMeterDataManager(PowerMeterDataManager):
        def _read_meter_loop(self):
            """Continuously read from the meter"""
            while self.running:
                try:
                    data = self.reader.read_data()
                    if data is not None:
                        self.meter_data = data
                        power = data.get('system', {}).get('power_kw', data.get('power_kw', 'N/A'))
                        logger.info(f"Updated readings: Power={power}kW (Simulated)")
                except Exception as e:
                    logger.error(f"Error in meter reading loop: {str(e)}")
                time.sleep(self.poll_interval)
    
    # Create data manager with simulator
    data_manager = CustomPowerMeterDataManager(reader, 2)  # Poll every 2 seconds
    
    # Create HTTP API server
    http_server = PowerMeterHTTPServer(CONFIG['HTTP_PORT'], data_manager)
    
    try:
        # Start test HTML page server (suppress the individual server log message)
        web_port = 8000
        
        # Temporarily increase log level to suppress static server message  
        static_logger = logging.getLogger('powermeter.web.static_server')
        original_level = static_logger.level
        static_logger.setLevel(logging.WARNING)
        
        start_static_server(web_port)
        
        # Restore original log level
        static_logger.setLevel(original_level)
        
        # Start components
        data_manager.start()
        http_server.start()
        
        # Single clean startup message
        logger.info("Test system available at http://localhost:{}/".format(CONFIG['HTTP_PORT']))
        logger.info("Default users available:")
        logger.info("   * admin/admin (full access)")
        logger.info("   * operator/operator (read/write)")  
        logger.info("   * viewer/viewer (read only)")
        logger.info("Data is simulated for testing purposes")
        
        logger.info("Press Ctrl+C to exit.")
        
        # Keep main thread alive until keyboard interrupt
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupt received. Shutting down.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        # Clean shutdown
        http_server.stop()
        data_manager.stop()
        reader.disconnect()
        logger.info("Test application shut down")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())