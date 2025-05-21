"""
API endpoints for power meter data
"""
import json
import binascii
import logging
import os
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from modbus.protocol import parse_response

logger = logging.getLogger('powermeter.api.endpoints')

class PowerMeterHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for power meter API endpoints"""
    
    # This will be set by the server
    data_manager = None
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/api/power':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS for testing
            self.end_headers()
            
            # Get the latest data from the data manager
            data = self.data_manager.get_data() if self.data_manager else {}
            self.wfile.write(json.dumps(data).encode('utf-8'))
        elif self.path.startswith('/api/register/'):
            # Extract register number from path
            try:
                register_num = int(self.path.split('/api/register/')[1])
                self.handle_register_request(register_num)
            except (ValueError, IndexError):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid register number')
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
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Serve HTML template
            template_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'web', 'templates', 'index.html'
            )
            
            try:
                with open(template_path, 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.wfile.write(b"<html><body><h1>Template not found</h1></body></html>")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')
    
    def handle_register_request(self, register_num):
        """Handle a request for a specific register"""
        if not self.data_manager or not hasattr(self.data_manager.reader, 'read_register'):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'No reader available')
            return
            
        try:
            # Convert from 4xxxx format to modbus address (subtract 40001)
            modbus_address = register_num
            if register_num >= 40001:
                modbus_address = register_num - 40001
                
            # Read the register
            register_value = self.data_manager.reader.read_register(register_num)
                
            if register_value is None:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(f'Failed to read register {register_num}'.encode('utf-8'))
                return
                    
            # Create response
            response = {
                'register': register_num,
                'modbus_address': modbus_address,
                'modbus_address_hex': hex(modbus_address),
                'value': register_value,
                'hex_value': hex(register_value),
                'timestamp': time.time()
            }
                    
            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            logger.error(f"Error reading register {register_num}: {str(e)}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode('utf-8'))
    
    def handle_registers_range_request(self, start, count):
        """Handle a request for a range of registers"""
        if not self.data_manager or not hasattr(self.data_manager.reader, 'read_registers'):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'No reader available')
            return
            
        try:
            # Read the registers
            registers = self.data_manager.reader.read_registers(start, count)
            
            if registers is None or len(registers) == 0:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(f'Failed to read registers {start}-{start+count-1}'.encode('utf-8'))
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
                'timestamp': time.time()
            }
                
            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error reading registers {start}-{start+count-1}: {str(e)}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode('utf-8'))
    
    def handle_modbus_command(self, command_hex):
        """Handle a request to send a raw Modbus command"""
        if not self.data_manager or not hasattr(self.data_manager.reader, 'modbus_client'):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'No Modbus client available')
            return
            
        try:
            # Convert hex string to bytes
            command = binascii.unhexlify(command_hex)
            
            logger.info(f"Sending raw Modbus command: {binascii.hexlify(command).decode()}")
            
            # Get the Modbus client
            client = self.data_manager.reader.modbus_client
            
            # Send the command
            response = client.send_command(command)
            
            if not response:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'No response received')
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
                'timestamp': time.time()
            }
                
            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except binascii.Error:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid hex string')
        except Exception as e:
            logger.error(f"Error sending Modbus command: {str(e)}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our own logging"""
        logger.debug(f"{self.client_address[0]} - {format % args}")