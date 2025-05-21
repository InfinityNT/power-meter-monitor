import signal
import sys
import time
import logging
import os

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config import CONFIG
from tests import PowerMeterSimulator, start_test_server
from powermeter import PowerMeterDataManager, PowerMeterHTTPServer

logger = logging.getLogger('powermeter.test')

def main():
    logger.info("Starting power meter test application with simulator")
    
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
                        logger.info(f"Updated readings: Power={data.get('system', {}).get('power_kw', 'N/A')}kW")
                except Exception as e:
                    logger.error(f"Error in meter reading loop: {str(e)}")
                time.sleep(self.poll_interval)
    
    # Create data manager with simulator
    data_manager = CustomPowerMeterDataManager(reader, 2)  # Poll every 2 seconds
    
    # Create HTTP API server
    http_server = PowerMeterHTTPServer(CONFIG['HTTP_PORT'], data_manager)
    
    try:
        # Start test HTML page server
        start_test_server(8000)
        logger.info("Test page available at http://localhost:8000/monitor.html")
        
        # Start components
        data_manager.start()
        http_server.start()
        
        logger.info(f"Test system running. HTTP API available at http://localhost:{CONFIG['HTTP_PORT']}/")
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