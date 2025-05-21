"""
HTTP server for exposing power meter data via API
"""
import threading
from http.server import ThreadingHTTPServer
import logging

from api.endpoints import PowerMeterHTTPHandler

logger = logging.getLogger('powermeter.api.server')

class PowerMeterHTTPServer:
    """HTTP server for exposing power meter data via API"""
    
    def __init__(self, port, data_manager):
        """
        Initialize the HTTP server
        
        Parameters:
        - port: TCP port to listen on
        - data_manager: PowerMeterDataManager instance
        """
        self.port = port
        self.data_manager = data_manager
        self.server = None
        
    def start(self):
        """Start the HTTP server"""
        # Set the data manager for the handler
        PowerMeterHTTPHandler.data_manager = self.data_manager
        
        # Create and start the server
        self.server = ThreadingHTTPServer(('', self.port), PowerMeterHTTPHandler)
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        logger.info(f"HTTP server started on port {self.port}")
        
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("HTTP server stopped")