"""
Core Modbus protocol functions including CRC calculation,
command building, and response parsing.
"""
import logging
import binascii

logger = logging.getLogger('powermeter.modbus.protocol')

def calculate_crc(data):
    """Calculate Modbus RTU CRC-16 for given data"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    # Return CRC as two bytes in little-endian order (low byte first)
    return crc.to_bytes(2, byteorder='little')

def build_command(device_address, function_code, register_address, register_count=1, register_values=None):
    """
    Build a Modbus RTU command
    
    Parameters:
    - device_address: Modbus device address (1-247)
    - function_code: Modbus function code (e.g., 3 for Read Holding Registers)
    - register_address: Register address (can be in 4xxxx format or direct)
    - register_count: Number of registers to read/write
    - register_values: List of values for write operations
    
    Returns:
    - bytearray containing the complete Modbus RTU command
    """
    # Convert register address from 4xxxx format if needed
    original_address = register_address
    if register_address >= 40001:
        register_address -= 40001
        
    # Log the address conversion for debugging
    logger.debug(f"Modbus command: Register {original_address} → Modbus address {register_address} (0x{register_address:04X})")
    logger.debug(f"High byte: 0x{(register_address >> 8) & 0xFF:02X}, Low byte: 0x{register_address & 0xFF:02X}")
        
    # Start building the command
    command = bytearray([
        device_address,
        function_code,
        (register_address >> 8) & 0xFF,  # Register address high byte
        register_address & 0xFF,         # Register address low byte
    ])
    
    # Add register count/values based on function code
    if function_code == 3 or function_code == 4:  # Read operations
        command.extend([
            (register_count >> 8) & 0xFF,    # Number of registers high byte
            register_count & 0xFF            # Number of registers low byte
        ])
    elif function_code == 6:  # Write Single Register
        if register_values and len(register_values) > 0:
            value = register_values[0]
            command.extend([
                (value >> 8) & 0xFF,   # Value high byte
                value & 0xFF           # Value low byte
            ])
        else:
            command.extend([0x00, 0x00])  # Default to zero if no value provided
    elif function_code == 16:  # Write Multiple Registers
        if register_values and len(register_values) > 0:
            command.extend([
                (register_count >> 8) & 0xFF,  # Number of registers high byte
                register_count & 0xFF,         # Number of registers low byte
                register_count * 2             # Byte count
            ])
            # Add each register value
            for value in register_values:
                command.extend([
                    (value >> 8) & 0xFF,  # Value high byte
                    value & 0xFF          # Value low byte
                ])
        else:
            # Default to writing zeros
            command.extend([
                (register_count >> 8) & 0xFF,  # Number of registers high byte
                register_count & 0xFF,         # Number of registers low byte
                register_count * 2             # Byte count
            ])
            # Add zero values
            for _ in range(register_count):
                command.extend([0x00, 0x00])
    
    # Calculate and append CRC
    crc = calculate_crc(command)
    command.extend(crc)
    
    # Log the complete command for debugging
    logger.debug(f"Complete command: {binascii.hexlify(command).decode()}")
    
    return command

def parse_response(command, response):
    """
    Parse a Modbus response into a structured format
    
    Parameters:
    - command: The original command bytes
    - response: The response bytes
    
    Returns:
    - Dictionary containing parsed response data
    """
    if not response or len(response) < 3:
        return {"error": "Invalid or empty response"}
        
    try:
        result = {
            "device_address": response[0],
            "function_code": response[1]
        }
        
        # Extract function code
        function_code = response[1]
        
        # Check if the highest bit of function code is set (error response)
        if (function_code & 0x80) != 0:
            result["error"] = True
            result["error_code"] = response[2]
            error_codes = {
                1: "Illegal Function",
                2: "Illegal Data Address",
                3: "Illegal Data Value",
                4: "Slave Device Failure",
                5: "Acknowledge",
                6: "Slave Device Busy",
                8: "Memory Parity Error",
                10: "Gateway Path Unavailable",
                11: "Gateway Target Device Failed to Respond"
            }
            result["error_message"] = error_codes.get(response[2], "Unknown Error")
            return result
        
        # Handle different function codes
        if function_code == 3 or function_code == 4:
            # Read holding/input registers response
            byte_count = response[2]
            register_count = byte_count // 2
            
            # Extract register values
            registers = []
            for i in range(register_count):
                high_byte = response[3 + i * 2]
                low_byte = response[3 + i * 2 + 1]
                value = (high_byte << 8) | low_byte
                registers.append({
                    "value": value,
                    "hex": hex(value)
                })
            
            # Get the register address from the request
            if len(command) >= 4:
                register_address = (command[2] << 8) | command[3]
                result["start_address"] = register_address
                
            result["byte_count"] = byte_count
            result["register_count"] = register_count
            result["registers"] = registers
            
        elif function_code == 6:
            # Write single register response
            register_address = (response[2] << 8) | response[3]
            register_value = (response[4] << 8) | response[5]
            
            result["register_address"] = register_address
            result["register_value"] = register_value
            result["register_value_hex"] = hex(register_value)
            
        elif function_code == 16:
            # Write multiple registers response
            register_address = (response[2] << 8) | response[3]
            register_count = (response[4] << 8) | response[5]
            
            result["register_address"] = register_address
            result["register_count"] = register_count
            
        return result
        
    except Exception as e:
        return {"error": f"Error parsing response: {str(e)}"}

def get_expected_response_length(command):
    """
    Calculate expected response length based on the command
    
    Parameters:
    - command: The Modbus command bytes
    
    Returns:
    - Expected length of the response in bytes
    """
    if len(command) < 2:
        return 256  # Default large value
        
    function_code = command[1]
    
    if function_code == 3 or function_code == 4:
        # Read holding/input registers
        # Expected response: address(1) + function(1) + byte_count(1) + data(n) + crc(2)
        # Calculate register count
        if len(command) >= 6:
            register_count = (command[4] << 8) | command[5]
            expected_length = 5 + (register_count * 2)
            return expected_length
    elif function_code == 6:
        # Write single register
        # Expected response: echo of request (8 bytes)
        return 8
    elif function_code == 16:
        # Write multiple registers
        # Expected response: address(1) + function(1) + addr_hi(1) + addr_lo(1) + count_hi(1) + count_lo(1) + crc(2)
        return 8
        
    # Default response size
    return 256