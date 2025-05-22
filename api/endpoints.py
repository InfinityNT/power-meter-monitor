"""
API endpoints for power meter data with authentication
Updated version of api/endpoints.py
"""
import json
import binascii
import logging
import os
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from functools import wraps

from modbus.protocol import parse_response
from core.auth import AuthenticationManager

logger = logging.getLogger('powermeter.api.endpoints')

# Global authentication manager
auth_manager = AuthenticationManager()

def require_auth(permission=None):
    """Decorator to require authentication for endpoints"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get authorization header
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_auth_error('No authentication token provided')
                return
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Validate session
            session = auth_manager.validate_session(token)
            if not session:
                self.send_auth_error('Invalid or expired session')
                return
            
            # Check permission if required
            if permission and not session.user.has_permission(permission):
                self.send_auth_error(f'Insufficient permissions. Required: {permission}')
                return
            
            # Store user info for use in endpoint
            self.current_user = session.user
            
            # Call the original function
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class PowerMeterHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for power meter API endpoints with authentication"""
    
    # This will be set by the server
    data_manager = None
    current_user = None
    
    def send_auth_error(self, message):
        """Send authentication error response"""
        self.send_response(401)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {'error': message, 'code': 'AUTH_REQUIRED'}
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def send_json_response(self, data, status_code=200):
        """Helper to send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/auth/login':
            self.handle_login()
        elif self.path == '/api/auth/logout':
            self.handle_logout()
        elif self.path == '/api/auth/change_password':
            self.handle_change_password()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/api/power':
            self.handle_power_data()
        elif self.path.startswith('/api/register/'):
            # Extract register number from path
            try:
                register_num = int(self.path.split('/api/register/')[1])
                self.handle_register_request(register_num)
            except (ValueError, IndexError):
                self.send_json_response({'error': 'Invalid register number'}, 400)
        elif self.path.startswith('/api/read_registers'):
            # Parse query string
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            
            start = int(params.get('start', ['44001'])[0])
            count = min(int(params.get('count', ['1'])[0]), 125)  # Limit to 125 registers
            
            self.handle_registers_range_request(start, count)
        elif self.path.startswith('/api/modbus_command'):
            # Parse query string
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            
            command_hex = params.get('command', [''])[0]
            self.handle_modbus_command(command_hex)
        elif self.path == '/api/auth/validate':
            self.handle_validate_session()
        elif self.path == '/api/auth/sessions':
            self.handle_get_sessions()
        elif self.path == '/' or self.path == '/index.html':
            self.serve_static_file('index.html')
        elif self.path == '/monitor.html':
            self.serve_static_file('monitor.html')
        elif self.path == '/login.html':
            self.serve_static_file('login.html')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')
    
    def handle_login(self):
        """Handle user login"""
        try:
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response({'error': 'No data provided'}, 400)
                return
                
            post_data = self.rfile.read(content_length)
            credentials = json.loads(post_data.decode('utf-8'))
            
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not username or not password:
                self.send_json_response({'error': 'Username and password required'}, 400)
                return
            
            # Authenticate
            auth_result = auth_manager.authenticate(username, password)
            
            if auth_result:
                logger.info(f"User '{username}' logged in successfully")
                self.send_json_response(auth_result)
            else:
                logger.warning(f"Failed login attempt for user '{username}'")
                self.send_json_response({'error': 'Invalid credentials'}, 401)
                
        except json.JSONDecodeError:
            self.send_json_response({'error': 'Invalid JSON data'}, 400)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    @require_auth()
    def handle_logout(self):
        """Handle user logout"""
        try:
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                auth_manager.logout(token)
            
            self.send_json_response({'message': 'Logged out successfully'})
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    def handle_validate_session(self):
        """Handle session validation"""
        try:
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_json_response({'valid': False, 'error': 'No token provided'}, 401)
                return
                
            token = auth_header[7:]
            session = auth_manager.validate_session(token)
            
            if session:
                self.send_json_response({
                    'valid': True,
                    'user': session.user.to_dict(),
                    'expires_at': session.expires_at.isoformat()
                })
            else:
                self.send_json_response({'valid': False, 'error': 'Invalid or expired session'}, 401)
                
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    @require_auth('admin')
    def handle_get_sessions(self):
        """Handle getting active sessions (admin only)"""
        try:
            sessions = auth_manager.get_active_sessions()
            self.send_json_response({
                'sessions': sessions,
                'count': len(sessions)
            })
        except Exception as e:
            logger.error(f"Get sessions error: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    @require_auth()
    def handle_change_password(self):
        """Handle password change"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response({'error': 'No data provided'}, 400)
                return
                
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            
            if not old_password or not new_password:
                self.send_json_response({'error': 'Old and new passwords required'}, 400)
                return
            
            success = auth_manager.change_password(
                self.current_user.username, 
                old_password, 
                new_password
            )
            
            if success:
                self.send_json_response({'message': 'Password changed successfully'})
            else:
                self.send_json_response({'error': 'Invalid old password'}, 400)
                
        except json.JSONDecodeError:
            self.send_json_response({'error': 'Invalid JSON data'}, 400)
        except Exception as e:
            logger.error(f"Change password error: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    @require_auth('read')
    def handle_power_data(self):
        """Handle power data request"""
        try:
            # Get the latest data from the data manager
            data = self.data_manager.get_data() if self.data_manager else {}
            
            # Add user info to response
            data['authenticated'] = True
            data['user'] = self.current_user.username
            data['role'] = self.current_user.role
            
            self.send_json_response(data)
        except Exception as e:
            logger.error(f"Power data error: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    @require_auth('read')
    def handle_register_request(self, register_num):
        """Handle a request for a specific register"""
        if not self.data_manager or not hasattr(self.data_manager.reader, 'read_register'):
            self.send_json_response({'error': 'No reader available'}, 500)
            return
            
        try:
            # Convert from 4xxxx format to modbus address (subtract 40001)
            modbus_address = register_num
            if register_num >= 40001:
                modbus_address = register_num - 40001
                
            # Read the register
            register_value = self.data_manager.reader.read_register(register_num)
                
            if register_value is None:
                self.send_json_response({'error': f'Failed to read register {register_num}'}, 404)
                return
                    
            # Create response
            response = {
                'register': register_num,
                'modbus_address': modbus_address,
                'modbus_address_hex': hex(modbus_address),
                'value': register_value,
                'hex_value': hex(register_value),
                'timestamp': time.time(),
                'read_by': self.current_user.username
            }
                    
            self.send_json_response(response)
                
        except Exception as e:
            logger.error(f"Error reading register {register_num}: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    @require_auth('read')
    def handle_registers_range_request(self, start, count):
        """Handle a request for a range of registers"""
        if not self.data_manager or not hasattr(self.data_manager.reader, 'read_registers'):
            self.send_json_response({'error': 'No reader available'}, 500)
            return
            
        try:
            # Read the registers
            registers = self.data_manager.reader.read_registers(start, count)
            
            if registers is None or len(registers) == 0:
                self.send_json_response({'error': f'Failed to read registers {start}-{start+count-1}'}, 404)
                return
                
            # Calculate modbus address
            modbus_start = start
            if start >= 40001:
                modbus_start = start - 40001
                
            # Create response
            response = {
                'start_register': start,
                'modbus_start': modbus_start,
                'modbus_address_hex': hex(modbus_start),
                'count': len(registers),
                'values': registers,
                'hex_values': [hex(val) for val in registers],
                'timestamp': time.time(),
                'read_by': self.current_user.username
            }
                
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error reading registers {start}-{start+count-1}: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    @require_auth('write')
    def handle_modbus_command(self, command_hex):
        """Handle a request to send a raw Modbus command"""
        if not self.data_manager or not hasattr(self.data_manager.reader, 'modbus_client'):
            self.send_json_response({'error': 'No Modbus client available'}, 500)
            return
            
        try:
            # Convert hex string to bytes
            command = binascii.unhexlify(command_hex)
            
            logger.info(f"User '{self.current_user.username}' sending Modbus command: {binascii.hexlify(command).decode()}")
            
            # Get the Modbus client
            client = self.data_manager.reader.modbus_client
            
            # Send the command
            response = client.send_command(command)
            
            if not response:
                self.send_json_response({'error': 'No response received'}, 404)
                return
                
            # Parse the response
            parsed = parse_response(command, response)
            
            # Convert bytes to list of integers
            response_list = list(response)
            
            response_data = {
                'command': list(command),
                'command_hex': binascii.hexlify(command).decode(),
                'response': response_list,
                'response_hex': binascii.hexlify(response).decode(),
                'parsed': parsed,
                'timestamp': time.time(),
                'executed_by': self.current_user.username
            }
                
            self.send_json_response(response_data)
            
        except binascii.Error:
            self.send_json_response({'error': 'Invalid hex string'}, 400)
        except Exception as e:
            logger.error(f"Error sending Modbus command: {str(e)}")
            self.send_json_response({'error': f'Server error: {str(e)}'}, 500)
    
    def serve_static_file(self, filename):
        """Serve static HTML files"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'web', 'templates', filename
        )
        
        try:
            with open(template_path, 'rb') as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"<html><body><h1>File not found</h1></body></html>")
    
    def log_message(self, format, *args):
        """Override to use our own logging"""
        logger.debug(f"{self.client_address[0]} - {format % args}")

# Function to clean up expired sessions periodically
def cleanup_sessions():
    """Clean up expired sessions"""
    auth_manager.cleanup_expired_sessions()

# Export for use in other modules
__all__ = ['PowerMeterHTTPHandler', 'auth_manager', 'cleanup_sessions']