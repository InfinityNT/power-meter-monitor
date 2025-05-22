/**
 * API communication functions
 * Fixed for proper cross-origin requests between ports 8000 and 8080
 */

/**
 * Base API URL - Always use port 8080 for API calls
 */
const API_BASE_URL = 'http://localhost:8080/api';

/**
 * Get authentication headers
 * @returns {Object} Headers object with auth token if available
 */
function getAuthHeaders() {
    const token = sessionStorage.getItem('powermeter_token');
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
}

/**
 * Handle fetch with authentication and error handling
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise} Promise resolving to response data
 */
async function authenticatedFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...getAuthHeaders(),
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        // Authentication failed, redirect to login on port 8080
        sessionStorage.removeItem('powermeter_token');
        sessionStorage.removeItem('powermeter_user');
        sessionStorage.removeItem('powermeter_role');
        window.location.href = 'http://localhost:8080/login.html';
        throw new Error('Authentication required');
    }
    
    if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
    }
    
    return response;
}

/**
 * Fetch current power meter readings
 * @returns {Promise} Promise resolving to meter data
 */
async function fetchMeterData() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/power`);
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
        const response = await authenticatedFetch(`${API_BASE_URL}/register/${registerNumber}`);
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
        const response = await authenticatedFetch(
            `${API_BASE_URL}/read_registers?start=${startRegister}&count=${count}`
        );
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
            
        const response = await authenticatedFetch(`${API_BASE_URL}/modbus_command?command=${hexCommand}`);
        return await response.json();
    } catch (error) {
        console.error('Error sending Modbus command:', error);
        throw error;
    }
}

// Export functions for use in other modules
export { fetchMeterData, readRegister, readRegisters, sendModbusCommand };