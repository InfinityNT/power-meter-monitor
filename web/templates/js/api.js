/**
 * API communication functions
 */

/**
 * Base API URL
 */
const API_BASE_URL = 'http://localhost:8080/api';

/**
 * Fetch current power meter readings
 * @returns {Promise} Promise resolving to meter data
 */
async function fetchMeterData() {
    try {
        const response = await fetch(`${API_BASE_URL}/power`);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching meter data:', error);
        throw error;
    }
}

/**
 * Read a specific register
 * @param {Number} registerNumber - Register number to read
 * @returns {Promise} Promise resolving to register data
 */
async function readRegister(registerNumber) {
    try {
        const response = await fetch(`${API_BASE_URL}/register/${registerNumber}`);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error reading register ${registerNumber}:`, error);
        throw error;
    }
}

/**
 * Read a range of registers
 * @param {Number} startRegister - Starting register number
 * @param {Number} count - Number of registers to read
 * @returns {Promise} Promise resolving to register data
 */
async function readRegisters(startRegister, count) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/read_registers?start=${startRegister}&count=${count}`
        );
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error reading registers ${startRegister}-${startRegister+count-1}:`, error);
        throw error;
    }
}

/**
 * Send a raw Modbus command
 * @param {Array} commandBytes - Array of command bytes
 * @returns {Promise} Promise resolving to command result
 */
async function sendModbusCommand(commandBytes) {
    try {
        // Convert bytes array to hex string
        const hexCommand = commandBytes.map(byte => 
            byte.toString(16).padStart(2, '0')).join('');
            
        const response = await fetch(`${API_BASE_URL}/modbus_command?command=${hexCommand}`);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error sending Modbus command:', error);
        throw error;
    }
}

// Export functions for use in other modules
export { fetchMeterData, readRegister, readRegisters, sendModbusCommand };