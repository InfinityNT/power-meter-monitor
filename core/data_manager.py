"""
Data manager for collecting and storing power meter data
"""
import time
import threading
import logging

logger = logging.getLogger('powermeter.core.data_manager')

class PowerMeterDataManager:
    """Manager for collecting and storing power meter data"""
    
    def __init__(self, reader, poll_interval=5):
        """
        Initialize the data manager
        
        Parameters:
        - reader: PowerMeterReader instance
        - poll_interval: Time between data collections in seconds
        """
        self.reader = reader
        self.poll_interval = poll_interval
        self.meter_data = {}
        self.running = False
        self._thread = None
    
    def get_data(self):
        """
        Get the latest meter data
        
        Returns:
        - Dictionary of the latest meter data
        """
        return self.meter_data
    
    def _read_meter_loop(self):
        """Background thread for continuously reading meter data"""
        from config.settings import CONFIG
        
        while self.running:
            try:
                # Use detailed data if configured, otherwise use basic data
                if CONFIG.get('DETAILED_DATA', False):
                    data = self.reader.read_detailed_data()
                else:
                    data = self.reader.read_basic_data()
                    
                if data is not None:
                    self.meter_data = data
                    # Log a summary of the data
                    power = data.get('system', {}).get('power_kw', data.get('power_kw', 'N/A'))
                    logger.info(f"Updated readings: Power={power}kW")
            except Exception as e:
                logger.error(f"Error in meter reading loop: {str(e)}")
                
            # Sleep until next reading
            time.sleep(self.poll_interval)
    
    def start(self):
        """Start collecting data"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Data manager already running")
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._read_meter_loop)
        self._thread.daemon = True
        self._thread.start()
        logger.info("Data manager started")
    
    def stop(self):
        """Stop collecting data"""
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=10)
            self._thread = None
        logger.info("Data manager stopped")