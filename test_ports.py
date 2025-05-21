import http.server
import socketserver
import threading
import socket

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Create a socket that connects to an external server
        # This doesn't actually establish a connection but helps determine
        # which local interface would be used
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"  # Fallback to localhost

class SimpleHTTPRequestHandlerWithIP(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Get server port
        port = self.server.server_address[1]
        
        # Create a simple HTML response showing IP and port
        html = f"""
        <html>
        <head>
            <title>Port {port} is open!</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
                .container {{ padding: 20px; background-color: #f0f0f0; border-radius: 10px; display: inline-block; }}
                .success {{ color: green; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">Success!</h1>
                <p>You've successfully connected to <strong>{get_local_ip()}</strong> on port <strong>{port}</strong></p>
                <p>This confirms that port {port} is open and accessible from your network.</p>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())

def start_server(port):
    """Start a server on the specified port."""
    handler = SimpleHTTPRequestHandlerWithIP
    
    # Allow the socket to be reused
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Server running on http://{get_local_ip()}:{port}")
        httpd.serve_forever()

def main():
    # Get and display the local IP
    local_ip = get_local_ip()
    print(f"Local IP address: {local_ip}")
    print("Starting servers on ports 8000 and 8080...")
    
    # Create and start threads for each server
    thread1 = threading.Thread(target=start_server, args=(8000,))
    thread2 = threading.Thread(target=start_server, args=(8080,))
    
    # Set as daemon threads so they exit when the main program exits
    thread1.daemon = True
    thread2.daemon = True
    
    thread1.start()
    thread2.start()
    
    print("\nServers are running!")
    print(f"To test from another device on your LAN, visit:")
    print(f"http://{local_ip}:8000")
    print(f"http://{local_ip}:8080")
    print("\nPress Ctrl+C to stop the servers...")
    
    try:
        # Keep the main thread alive
        thread1.join()
    except KeyboardInterrupt:
        print("\nServers stopped.")

if __name__ == "__main__":
    main()