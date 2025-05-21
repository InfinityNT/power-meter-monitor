"""
Modbus client for communicating with power meters over serial connections
"""
import logging
import time
import binascii
import serial
from modbus.protocol import build_command, parse_response, get_expected_response_length

logger = logging.getLogger('powermeter.modbus.client')

class ModbusClient:
    """Modbus RTU client for communication with power meters"""
    
    def __init__(self, port, baud_rate, device_address=1, timeout=1):
        self.port = port
        self.baud_rate = baud_rate
        self.device_address = device_address
        self.timeout = timeout
        self.serial = None
        
    def connect(self):
        """Connect to the serial port"""
        try:
            from config.settings import CONFIG
            logger.info(f"Connecting to device on {self.port} at {self.baud_rate} baud")
            
            # Get advanced serial settings from config
            bytesize_map = {
                5: serial.FIVEBITS,
                6: serial.SIXBITS,
                7: serial.SEVENBITS,
                8: serial.EIGHTBITS
            }
            bytesize = bytesize_map.get(CONFIG.get('SERIAL_BYTESIZE', 8), serial.EIGHTBITS)
            
            parity_map = {
                'N': serial.PARITY_NONE,
                'E': serial.PARITY_EVEN,
                'O': serial.PARITY_ODD,
                'M': serial.PARITY_MARK,
                'S': serial.PARITY_SPACE
            }
            parity = parity_map.get(CONFIG.get('SERIAL_PARITY', 'N'), serial.PARITY_NONE)
            
            stopbits_map = {
                1: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO
            }
            stopbits = stopbits_map.get(CONFIG.get('SERIAL_STOPBITS', 1), serial.STOPBITS_ONE)
            
            # Create serial connection with all settings
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                xonxoff=CONFIG.get('SERIAL_XONXOFF', False),
                rtscts=CONFIG.get('SERIAL_RTSCTS', False),
                dsrdtr=CONFIG.get('SERIAL_DSRDTR', False)
            )
            
            logger.info(f"Successfully connected to {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.port}: {str(e)}")
            return False
            
    def disconnect(self):
        """Disconnect from the serial port"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info("Serial connection closed")
    
    def send_command(self, command):
        """
        Send a pre-built Modbus command and return the response
        
        Parameters:
        - command: The command bytes to send
        
        Returns:
        - Response bytes or None if error
        """
        if not self.serial or not self.serial.is_open:
            if not self.connect():
                return None
                
        try:
            # Clear any pending data
            self.serial.reset_input_buffer()
            
            # Send the command
            self.serial.write(command)
            
            # Calculate expected response length
            expected_length = get_expected_response_length(command)
            
            # Read response
            response = self.serial.read(expected_length)
            
            # Log the response
            logger.debug(f"Received response: {binascii.hexlify(response).decode()}")
            
            return response
        except Exception as e:
            logger.error(f"Error sending command: {str(e)}")
            return None
    
    def read_registers(self, register_address, register_count=1):
        """
        Read holding registers from the device
        
        Parameters:
        - register_address: Starting register address
        - register_count: Number of registers to read
        
        Returns:
        - List of register values or None if error
        """
        try:
            # Build the command
            command = build_command(
                self.device_address, 
                3,  # Function code 3 = Read Holding Registers
                register_address, 
                register_count
            )
            
            # Send the command
            response = self.send_command(command)
            
            if not response or len(response) < 3:
                logger.warning(f"Invalid response when reading registers from {register_address}")
                return None
                
            # Check for Modbus error response
            if (response[1] & 0x80) != 0:
                error_code = response[2]
                logger.error(f"Modbus error when reading registers: function={response[1]}, error={error_code}")
                return None
                
            # Parse the response
            byte_count = response[2]
            
            # Extract register values
            registers = []
            for i in range(byte_count // 2):
                high_byte = response[3 + i * 2]
                low_byte = response[3 + i * 2 + 1]
                value = (high_byte << 8) | low_byte
                registers.append(value)
                
            logger.debug(f"Read {len(registers)} registers from {register_address}: {registers}")
            return registers
            
        except Exception as e:
            logger.error(f"Error reading registers from {register_address}: {str(e)}")
            return None
    
    def write_register(self, register_address, value):
        """
        Write a single register value
        
        Parameters:
        - register_address: Register address to write to
        - value: Value to write
        
        Returns:
        - True if successful, False otherwise
        """
        try:
            # Build the command
            command = build_command(
                self.device_address,
                6,  # Function code 6 = Write Single Register
                register_address,
                1,  # Count is always 1 for single register write
                [value]  # Value to write
            )
            
            # Send the command
            response = self.send_command(command)
            
            if not response or len(response) < 6:
                logger.warning(f"Invalid response when writing to register {register_address}")
                return False
                
            # Check for Modbus error response
            if (response[1] & 0x80) != 0:
                error_code = response[2]
                logger.error(f"Modbus error when writing register: function={response[1]}, error={error_code}")
                return False
                
            # Check that the response matches the request
            if (response[2] != command[2] or response[3] != command[3] or 
                response[4] != command[4] or response[5] != command[5]):
                logger.warning(f"Response mismatch when writing to register {register_address}")
                return False
                
            logger.info(f"Successfully wrote value {value} to register {register_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing to register {register_address}: {str(e)}")
            return False
    
    def execute_raw_command(self, command_bytes):
        """
        Execute a raw Modbus command and return the response
        
        Parameters:
        - command_bytes: Raw command bytes to send
        
        Returns:
        - Dictionary with parsed response and raw bytes
        """
        try:
            # Send the command
            response = self.send_command(command_bytes)
            
            if not response:
                return {
                    "error": "No response received",
                    "raw_response": None
                }
                
            # Parse the response
            parsed = parse_response(command_bytes, response)
            
            return {
                "parsed": parsed,
                "raw_response": list(response),
                "raw_hex": binascii.hexlify(response).decode()
            }
            
        except Exception as e:
            logger.error(f"Error executing raw command: {str(e)}")
            return {
                "error": str(e),
                "raw_response": None
            }