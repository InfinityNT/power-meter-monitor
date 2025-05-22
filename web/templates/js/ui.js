/**
 * UI initialization and event handling
 * Complete version of ui.js
 */
import { updateDashboard } from './dashboard.js';
import { readRegister, readRegisters, sendModbusCommand } from './api.js';
import { buildModbusCommand, FUNCTION_CODES } from './modbus.js';

/**
 * Initialize the UI
 */
function initializeUI() {
    // Set up tab navigation
    setupTabs();
    
    // Set up refresh button
    document.getElementById('refreshBtn').addEventListener('click', updateDashboard);
    
    // Set up register query buttons
    document.getElementById('readRegisterBtn').addEventListener('click', handleReadRegister);
    document.getElementById('readRegisterRangeBtn').addEventListener('click', handleReadRegisterRange);
    
    // Set up Modbus command buttons
    document.getElementById('buildModbusCommandBtn').addEventListener('click', handleBuildModbusCommand);
    document.getElementById('sendModbusCommandBtn').addEventListener('click', handleSendModbusCommand);
    
    // Initial dashboard update
    updateDashboard();
    
    // Set up automatic refresh every 5 seconds
    setInterval(updateDashboard, 5000);
}

/**
 * Set up tab navigation
 */
function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            const contentId = tab.getAttribute('data-tab');
            document.getElementById(contentId).classList.add('active');
        });
    });
}

/**
 * Handle reading a single register
 */
async function handleReadRegister() {
    const registerNum = document.getElementById('registerInput').value;
    
    if (!registerNum || isNaN(parseInt(registerNum))) {
        alert('Please enter a valid register number');
        return;
    }
    
    document.getElementById('registerNumber').textContent = 'Loading...';
    document.getElementById('registerValue').textContent = 'Loading...';
    document.getElementById('registerTimestamp').textContent = 'Loading...';
    
    try {
        const data = await readRegister(parseInt(registerNum));
        
        document.getElementById('registerNumber').textContent = data.register;
        document.getElementById('registerValue').textContent = data.value;
        
        // Add hex representation
        const hexValue = data.hex_value || ('0x' + data.value.toString(16).toUpperCase());
        document.getElementById('registerValue').textContent += ` (${hexValue})`;
        
        const date = new Date(data.timestamp * 1000);
        document.getElementById('registerTimestamp').textContent = date.toLocaleString();
    } catch (error) {
        console.error('Error reading register:', error);
        document.getElementById('registerNumber').textContent = registerNum;
        document.getElementById('registerValue').textContent = 'Error: ' + error.message;
        document.getElementById('registerTimestamp').textContent = '--';
    }
}

/**
 * Handle reading a range of registers
 */
async function handleReadRegisterRange() {
    const startRegister = document.getElementById('startRegisterInput').value;
    const count = document.getElementById('countRegisterInput').value;
    
    if (!startRegister || isNaN(parseInt(startRegister)) || !count || isNaN(parseInt(count))) {
        alert('Please enter valid start register and count');
        return;
    }
    
    // Clear previous results
    document.getElementById('registerTableBody').innerHTML = 
        '<tr><td colspan="3">Loading...</td></tr>';
    
    try {
        const data = await readRegisters(parseInt(startRegister), parseInt(count));
        
        // Build table with results
        const tableBody = document.getElementById('registerTableBody');
        tableBody.innerHTML = '';
        
        data.values.forEach((value, index) => {
            const registerNum = data.start_register + index;
            const row = document.createElement('tr');
            
            // Highlight register 44602 (scalar value)
            if (registerNum === 44602) {
                row.classList.add('highlighted');
            }
            
            const registerCell = document.createElement('td');
            registerCell.textContent = registerNum;
            
            const valueCell = document.createElement('td');
            valueCell.textContent = value;
            
            const hexCell = document.createElement('td');
            hexCell.textContent = '0x' + value.toString(16).toUpperCase();
            
            row.appendChild(registerCell);
            row.appendChild(valueCell);
            row.appendChild(hexCell);
            
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error reading registers:', error);
        document.getElementById('registerTableBody').innerHTML = 
            `<tr><td colspan="3">Error: ${error.message}</td></tr>`;
    }
}

/**
 * Handle building a Modbus command
 */
function handleBuildModbusCommand() {
    // Get input values
    const deviceAddress = parseInt(document.getElementById('modbusAddress').value);
    const functionCode = parseInt(document.getElementById('modbusFunctionCode').value);
    let registerAddress = parseInt(document.getElementById('modbusRegisterAddress').value);
    const registerCount = parseInt(document.getElementById('modbusRegisterCount').value);
    
    // Build command using modbus module
    const commandInfo = buildModbusCommand(deviceAddress, functionCode, registerAddress, registerCount);
    
    // Display the command
    document.getElementById('modbusCommand').textContent = commandInfo.hexCommand;
    
    // Also display detailed address information
    const noteElement = document.createElement('div');
    noteElement.className = 'register-note';
    noteElement.innerHTML = `
        <p><small>Register: ${commandInfo.originalAddress}, Modbus Address: ${commandInfo.modbusAddress} (${commandInfo.hexAddress})</small></p>
        <p><small>High Byte: ${commandInfo.highByte}, Low Byte: ${commandInfo.lowByte}</small></p>
    `;
    
    const commandDisplay = document.getElementById('modbusCommand');
    if (commandDisplay.nextElementSibling?.className === 'register-note') {
        commandDisplay.nextElementSibling.remove();
    }
    commandDisplay.parentNode.insertBefore(noteElement, commandDisplay.nextSibling);
}

/**
 * Handle sending a Modbus command
 */
async function handleSendModbusCommand() {
    // First build the command
    handleBuildModbusCommand();
    
    // Get the command info
    const deviceAddress = parseInt(document.getElementById('modbusAddress').value);
    const functionCode = parseInt(document.getElementById('modbusFunctionCode').value);
    const registerAddress = parseInt(document.getElementById('modbusRegisterAddress').value);
    const registerCount = parseInt(document.getElementById('modbusRegisterCount').value);
    
    const commandInfo = buildModbusCommand(deviceAddress, functionCode, registerAddress, registerCount);
    
    // Send to server
    document.getElementById('modbusResponse').textContent = 'Sending command...';
    document.getElementById('modbusParsedResponse').textContent = 'Waiting for response...';
    
    try {
        const response = await sendModbusCommand(commandInfo.command);
        
        // Display the raw response
        const responseHex = response.response.map(byte => 
            byte.toString(16).padStart(2, '0').toUpperCase()).join(' ');
        document.getElementById('modbusResponse').textContent = responseHex;
        
        // Parse and display the formatted response
        parseAndDisplayResponse(response.response, registerAddress);
    } catch (error) {
        console.error('Error sending Modbus command:', error);
        document.getElementById('modbusResponse').textContent = 'Error: ' + error.message;
        document.getElementById('modbusParsedResponse').textContent = 'Failed to get response';
    }
}

/**
 * Parse and display Modbus response
 */
function parseAndDisplayResponse(response, startRegister) {
    // Basic validation
    if (!response || response.length < 3) {
        document.getElementById('modbusParsedResponse').textContent = 'Invalid or empty response';
        return;
    }
    
    try {
        const deviceAddress = response[0];
        const functionCode = response[1];
        
        // Parse based on function code
        if (functionCode === 3 || functionCode === 4) {
            // Read holding/input registers response
            const byteCount = response[2];
            const registerCount = byteCount / 2;
            
            let html = `<p>Device: ${deviceAddress}, Function: ${functionCode}, Byte Count: ${byteCount}</p>`;
            html += '<table><thead><tr><th>Register</th><th>Value (Dec)</th><th>Value (Hex)</th></tr></thead><tbody>';
            
            // Extract register values
            for (let i = 0; i < registerCount; i++) {
                const highByte = response[3 + i * 2];
                const lowByte = response[3 + i * 2 + 1];
                const value = (highByte << 8) | lowByte;
                
                html += `<tr>
                    <td>${startRegister + i}</td>
                    <td>${value}</td>
                    <td>0x${value.toString(16).toUpperCase().padStart(4, '0')}</td>
                </tr>`;
            }
            
            html += '</tbody></table>';
            document.getElementById('modbusParsedResponse').innerHTML = html;
        } else if (functionCode === 6) {
            // Write single register response
            const registerAddress = (response[2] << 8) | response[3];
            const registerValue = (response[4] << 8) | response[5];
            
            document.getElementById('modbusParsedResponse').innerHTML = 
                `<p>Device: ${deviceAddress}, Function: ${functionCode}</p>
                <p>Register Address: ${registerAddress}, Value: ${registerValue} (0x${registerValue.toString(16).toUpperCase()})</p>`;
        } else if (functionCode === 16) {
            // Write multiple registers response
            const registerAddress = (response[2] << 8) | response[3];
            const registerCount = (response[4] << 8) | response[5];
            
            document.getElementById('modbusParsedResponse').innerHTML = 
                `<p>Device: ${deviceAddress}, Function: ${functionCode}</p>
                <p>Starting Address: ${registerAddress}, Registers Written: ${registerCount}</p>`;
        } else {
            // Error or unknown function code
            document.getElementById('modbusParsedResponse').textContent = 
                `Unknown or error function code: ${functionCode}`;
        }
    } catch (e) {
        document.getElementById('modbusParsedResponse').textContent = 
            `Error parsing response: ${e.message}`;
    }
}

// Export for use in other modules
export { initializeUI, setupTabs, handleReadRegister, handleReadRegisterRange, handleBuildModbusCommand, handleSendModbusCommand };