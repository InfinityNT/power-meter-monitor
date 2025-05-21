"""
Static file server for web interface
"""
import http.server
import socketserver
import os
import threading
import logging

logger = logging.getLogger('powermeter.web.static_server')

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
    os.chdir(web_dir)
    
    # Create and start HTTP server
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    logger.info(f"Serving web interface at http://localhost:{port}/index.html")
    httpd.serve_forever()

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