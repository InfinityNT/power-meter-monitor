"""
Static file server for web interface
Updated to suppress duplicate log messages
"""
import http.server
import socketserver
import os
import threading
import logging

logger = logging.getLogger('powermeter.web.static_server')

class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler that doesn't log every request"""
    
    def log_message(self, format, *args):
        """Override to suppress request logging"""
        # Only log errors
        if format.startswith('code 404') or format.startswith('code 500'):
            logger.warning(f"{self.client_address[0]} - {format % args}")

def serve_static_files(port=8000):
    """
    Serve static files from the web/templates directory
    
    Parameters:
    - port: TCP port to listen on
    """
    # Get the web templates directory
    web_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'web', 'templates'
    )
    
    # Ensure the directory exists
    if not os.path.exists(web_dir):
        logger.error(f"Web templates directory does not exist: {web_dir}")
        return
    
    # Change to web directory
    original_dir = os.getcwd()
    os.chdir(web_dir)
    
    try:
        # Create and start HTTP server with quiet handler
        handler = QuietHTTPRequestHandler
        httpd = socketserver.TCPServer(("", port), handler)
        
        # Only log startup message if explicitly requested
        if logger.level <= logging.INFO:
            logger.info(f"Serving web interface at http://localhost:{port}/index.html")
        
        httpd.serve_forever()
    finally:
        # Restore original directory
        os.chdir(original_dir)

def start_static_server(port=8000):
    """
    Start a static file server in a separate thread
    
    Parameters:
    - port: TCP port to listen on
    
    Returns:
    - Thread object for the server
    """
    server_thread = threading.Thread(target=serve_static_files, args=(port,))
    server_thread.daemon = True
    server_thread.start()
    return server_thread