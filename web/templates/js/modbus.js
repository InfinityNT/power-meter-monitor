/**
 * Modbus protocol functions for the web interface
 */

// Constants
const FUNCTION_CODES = {
    READ_HOLDING_REGISTERS: 3,
    READ_INPUT_REGISTERS: 4,
    WRITE_SINGLE_REGISTER: 6,
    WRITE_MULTIPLE_REGISTERS: 16
};

/**
 * Calculate Modbus RTU CRC-16 for a given array of bytes
 * @param {Array} data - Array of byte values
 * @returns {Array} Two-byte CRC in little-endian order
 */
function calculateCRC(data) {
    let crc = 0xFFFF;
    
    for (let i = 0; i < data.length; i++) {
        crc ^= data[i];
        
        for (let j = 0; j < 8; j++) {
            if (crc & 0x0001) {
                crc = (crc >> 1) ^ 0xA001;
            } else {
                crc >>= 1;
            }
        }
    }
    
    // Return as two bytes (low byte first)
    return [(crc & 0xFF), (crc >> 8)];
}

/**
 * Build a Modbus command
 * @param {Number} deviceAddress - Device address (1-247)
 * @param {Number} functionCode - Function code (3, 4, 6, 16)
 * @param {Number} registerAddress - Register address (can be 4xxxx or direct)
 * @param {Number} registerCount - Number of registers to read/write
 * @param {Array} registerValues - Register values for write operations
 * @returns {Object} Command object with bytes and metadata
 */
function buildModbusCommand(deviceAddress, functionCode, registerAddress, registerCount = 1, registerValues = null) {
    // Convert from 4xxxx format if needed
    const originalAddress = registerAddress;
    if (registerAddress >= 40001) {
        registerAddress = registerAddress - 40001;
    }
    
    // Create command array
    const command = [
        deviceAddress,
        functionCode,
        (registerAddress >> 8) & 0xFF,  // Register address high byte
        registerAddress & 0xFF,         // Register address low byte
    ];
    
    // Add register count or value based on function code
    if (functionCode === FUNCTION_CODES.READ_HOLDING_REGISTERS || 
        functionCode === FUNCTION_CODES.READ_INPUT_REGISTERS) {
        command.push((registerCount >> 8) & 0xFF);  // Count high byte
        command.push(registerCount & 0xFF);         // Count low byte
    } else if (functionCode === FUNCTION_CODES.WRITE_SINGLE_REGISTER) {
        const value = registerValues && registerValues.length ? registerValues[0] : 0;
        command.push((value >> 8) & 0xFF);  // Value high byte
        command.push(value & 0xFF);         // Value low byte
    } else if (functionCode === FUNCTION_CODES.WRITE_MULTIPLE_REGISTERS) {
        command.push((registerCount >> 8) & 0xFF);  // Count high byte
        command.push(registerCount & 0xFF);         // Count low byte
        command.push(registerCount * 2);            // Byte count
        
        // Add values
        if (registerValues && registerValues.length) {
            for (let i = 0; i < registerCount; i++) {
                const value = i < registerValues.length ? registerValues[i] : 0;
                command.push((value >> 8) & 0xFF);  // Value high byte
                command.push(value & 0xFF);         // Value low byte
            }
        } else {
            // Default to zeros
            for (let i = 0; i < registerCount; i++) {
                command.push(0x00);  // Value high byte
                command.push(0x00);  // Value low byte
            }
        }
    }
    
    // Calculate and add CRC
    const crc = calculateCRC(command);
    command.push(crc[0], crc[1]);
    
    // Return command info with metadata for display
    return {
        command: command,
        originalAddress: originalAddress,
        modbusAddress: registerAddress,
        hexAddress: '0x' + registerAddress.toString(16).toUpperCase().padStart(4, '0'),
        highByte: '0x' + ((registerAddress >> 8) & 0xFF).toString(16).toUpperCase().padStart(2, '0'),
        lowByte: '0x' + (registerAddress & 0xFF).toString(16).toUpperCase().padStart(2, '0'),
        hexCommand: command.map(byte => byte.toString(16).padStart(2, '0').toUpperCase()).join(' ')
    };
}

// Export functions for use in other modules
export { calculateCRC, buildModbusCommand, FUNCTION_CODES };