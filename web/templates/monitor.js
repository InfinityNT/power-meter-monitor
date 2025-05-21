// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Set up tab navigation
    setupTabs();
    
    // Initial fetch
    fetchReadings();
    
    // Set up refresh button
    document.getElementById('refreshBtn').addEventListener('click', fetchReadings);
    
    // Set up automatic refresh every 5 seconds
    setInterval(fetchReadings, 5000);

    // Set up register query button
    document.getElementById('readRegisterBtn').addEventListener('click', readRegister);
    document.getElementById('readRegisterRangeBtn').addEventListener('click', readRegisterRange);

    // Setup Modbus command buttons
    document.getElementById('buildModbusCommandBtn').addEventListener('click', buildModbusCommand);
    document.getElementById('sendModbusCommandBtn').addEventListener('click', sendModbusCommand);
});

// Set up tab navigation
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

// Fetch power meter readings from the API
function fetchReadings() {
    document.getElementById('status').textContent = 'Connecting...';
    
    fetch('http://localhost:8080/api/power')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update the UI with the received data
            updateUIWithData(data);
            
            // Show all data in the raw data section
            document.getElementById('rawDataContent').textContent = 
                JSON.stringify(data, null, 2);
            
            const simMsg = data.simulated ? ' (Simulated Data)' : '';
            document.getElementById('status').textContent = 'Connected' + simMsg;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('status').textContent = 'Error connecting to API';
        });
}

// Update the UI with the received data
function updateUIWithData(data) {
    // Update system values
    document.getElementById('power_kw').textContent = formatValue(data.system?.power_kw || data.power_kw);
    document.getElementById('reactive_power_kvar').textContent = formatValue(data.system?.reactive_power_kvar || data.reactive_power_kvar);
    document.getElementById('apparent_power_kva').textContent = formatValue(data.system?.apparent_power_kva || data.apparent_power_kva);
    document.getElementById('energy_kwh').textContent = formatValue(data.system?.energy_kwh || data.energy_kwh);
    document.getElementById('power_factor').textContent = formatValue(data.system?.displacement_pf || data.power_factor);
    document.getElementById('current_avg').textContent = formatValue(data.system?.current_avg || data.current_avg);
    document.getElementById('voltage_ll_avg').textContent = formatValue(data.system?.voltage_ll_avg || data.voltage_ll_avg);
    document.getElementById('voltage_ln_avg').textContent = formatValue(data.system?.voltage_ln_avg || data.voltage_ln_avg);
    document.getElementById('frequency').textContent = formatValue(data.frequency);
    
    // Update phase values if available
    if (data.phase_1) {
        document.getElementById('phase1_power').textContent = formatValue(data.phase_1.power_kw);
        document.getElementById('phase1_current').textContent = formatValue(data.phase_1.current);
        document.getElementById('phase1_voltage').textContent = formatValue(data.phase_1.voltage_ln);
        document.getElementById('phase1_pf').textContent = formatValue(data.phase_1.displacement_pf);
        
        document.getElementById('phase2_power').textContent = formatValue(data.phase_2.power_kw);
        document.getElementById('phase2_current').textContent = formatValue(data.phase_2.current);
        document.getElementById('phase2_voltage').textContent = formatValue(data.phase_2.voltage_ln);
        document.getElementById('phase2_pf').textContent = formatValue(data.phase_2.displacement_pf);
        
        document.getElementById('phase3_power').textContent = formatValue(data.phase_3.power_kw);
        document.getElementById('phase3_current').textContent = formatValue(data.phase_3.current);
        document.getElementById('phase3_voltage').textContent = formatValue(data.phase_3.voltage_ln);
        document.getElementById('phase3_pf').textContent = formatValue(data.phase_3.displacement_pf);
    }
    
    // Update scalar and multiplier information
    if (data.data_scalar !== undefined) {
        document.getElementById('data_scalar').textContent = data.data_scalar;
    }
    if (data.multipliers) {
        document.getElementById('power_multiplier').textContent = data.multipliers.power;
        document.getElementById('voltage_multiplier').textContent = data.multipliers.voltage;
        document.getElementById('current_multiplier').textContent = data.multipliers.current;
        document.getElementById('pf_multiplier').textContent = data.multipliers.pf;
        document.getElementById('freq_multiplier').textContent = data.multipliers.frequency;
    }
    
    // Update raw values
    if (data.raw_values) {
        document.getElementById('raw_frequency').textContent = data.raw_values.frequency || '--';
        document.getElementById('raw_voltage_ll').textContent = data.raw_values.voltage_ll || '--';
        document.getElementById('raw_voltage_ln').textContent = data.raw_values.voltage_ln || '--';
        document.getElementById('raw_current').textContent = data.raw_values.current || '--';
        document.getElementById('raw_power').textContent = data.raw_values.power || '--';
        document.getElementById('raw_pf').textContent = data.raw_values.pf || '--';
    }
    
    // Update timestamp
    const date = new Date(data.timestamp * 1000);
    document.getElementById('timestamp').textContent = date.toLocaleString();
}

// Format a value to 2 decimal places or show '--' if undefined
function formatValue(value) {
    if (value === undefined || value === null) {
        return '--';
    }
    
    // Convert to number if it's a string
    const numValue = Number(value);
    
    // Handle large values (millions+)
    if (numValue >= 1000000) {
        // Format as millions with 2 decimal places
        return (numValue / 1000000).toFixed(2) + ' M';
    } else if (numValue >= 1000) {
        // Format as thousands with 2 decimal places
        return (numValue / 1000).toFixed(2) + ' K';
    } else {
        // Regular formatting for smaller values
        return numValue.toFixed(2);
    }
}

// Function to read a single register
function readRegister() {
    const registerNum = document.getElementById('registerInput').value;
    
    if (!registerNum || isNaN(parseInt(registerNum))) {
        alert('Please enter a valid register number');
        return;
    }
    
    document.getElementById('registerNumber').textContent = 'Loading...';
    document.getElementById('registerValue').textContent = 'Loading...';
    document.getElementById('registerTimestamp').textContent = 'Loading...';
    
    fetch(`http://localhost:8080/api/register/${registerNum}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('registerNumber').textContent = data.register;
            document.getElementById('registerValue').textContent = data.value;
            
            // Add hex representation
            const hexValue = '0x' + data.value.toString(16).toUpperCase();
            document.getElementById('registerValue').textContent += ` (${hexValue})`;
            
            const date = new Date(data.timestamp * 1000);
            document.getElementById('registerTimestamp').textContent = date.toLocaleString();
        })
        .catch(error => {
            console.error('Error fetching register:', error);
            document.getElementById('registerNumber').textContent = registerNum;
            document.getElementById('registerValue').textContent = 'Error: ' + error.message;
            document.getElementById('registerTimestamp').textContent = '--';
        });
}

// Function to read a range of registers
function readRegisterRange() {
    const startRegister = document.getElementById('startRegisterInput').value;
    const count = document.getElementById('countRegisterInput').value;
    
    if (!startRegister || isNaN(parseInt(startRegister)) || !count || isNaN(parseInt(count))) {
        alert('Please enter valid start register and count');
        return;
    }
    
    // Clear previous results
    document.getElementById('registerTableBody').innerHTML = 
        '<tr><td colspan="3">Loading...</td></tr>';
    
    fetch(`http://localhost:8080/api/read_registers?start=${startRegister}&count=${count}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
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
        })
        .catch(error => {
            console.error('Error fetching registers:', error);
            document.getElementById('registerTableBody').innerHTML = 
                `<tr><td colspan="3">Error: ${error.message}</td></tr>`;
        });
}

// Function to calculate Modbus RTU CRC-16
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

// Function to build a Modbus command
function buildModbusCommand() {
    // Get input values
    const deviceAddress = parseInt(document.getElementById('modbusAddress').value);
    const functionCode = parseInt(document.getElementById('modbusFunctionCode').value);
    let registerAddress = parseInt(document.getElementById('modbusRegisterAddress').value);
    const registerCount = parseInt(document.getElementById('modbusRegisterCount').value);
    
    // Check if register address is in 4xxxx format and convert correctly
    if (registerAddress >= 40001 && registerAddress <= 49999) {
        registerAddress = registerAddress - 40001; // Correct offset for 4xxxx registers
    }
    
    // Create command array
    const command = [
        deviceAddress,
        functionCode,
        (registerAddress >> 8) & 0xFF,  // Register address high byte
        registerAddress & 0xFF,         // Register address low byte
    ];
    
    // Add register count or value based on function code
    if (functionCode === 3 || functionCode === 4) {
        // Read functions - add register count
        command.push((registerCount >> 8) & 0xFF);  // Count high byte
        command.push(registerCount & 0xFF);         // Count low byte
    } else if (functionCode === 6) {
        // Write single register - add register value
        command.push((registerCount >> 8) & 0xFF);  // Value high byte
        command.push(registerCount & 0xFF);         // Value low byte
    } else if (functionCode === 16) {
        // Write multiple registers - we'll simplify by writing the same value to all registers
        command.push((registerCount >> 8) & 0xFF);  // Count high byte
        command.push(registerCount & 0xFF);         // Count low byte
        command.push(registerCount * 2);            // Byte count
        
        // Add values (all the same for simplicity)
        for (let i = 0; i < registerCount; i++) {
            command.push(0x00);  // Value high byte (0)
            command.push(0x00);  // Value low byte (0)
        }
    }
    
    // Calculate and add CRC
    const crc = calculateCRC(command);
    command.push(crc[0], crc[1]);
    
    // Display the command
    displayCommand(command);
    
    // Also display detailed address information
    const originalAddress = document.getElementById('modbusRegisterAddress').value;
    const modbusAddress = registerAddress;
    const hexAddress = '0x' + modbusAddress.toString(16).toUpperCase().padStart(4, '0');
    const highByte = '0x' + ((modbusAddress >> 8) & 0xFF).toString(16).toUpperCase().padStart(2, '0');
    const lowByte = '0x' + (modbusAddress & 0xFF).toString(16).toUpperCase().padStart(2, '0');
    
    const noteElement = document.createElement('div');
    noteElement.className = 'register-note';
    noteElement.innerHTML = `
        <p><small>Register: ${originalAddress}, Modbus Address: ${modbusAddress} (${hexAddress})</small></p>
        <p><small>High Byte: ${highByte}, Low Byte: ${lowByte}</small></p>
    `;
    
    const commandDisplay = document.getElementById('modbusCommand');
    if (commandDisplay.nextElementSibling?.className === 'register-note') {
        commandDisplay.nextElementSibling.remove();
    }
    commandDisplay.parentNode.insertBefore(noteElement, commandDisplay.nextSibling);
    
    return command;
}

// Function to display command as hex string
function displayCommand(command) {
    // Convert to hex string
    const hexString = command.map(byte => byte.toString(16).padStart(2, '0').toUpperCase()).join(' ');
    
    // Display in the UI
    document.getElementById('modbusCommand').textContent = hexString;
}

// Function to send the Modbus command to the server
function sendModbusCommand() {
    // First build the command
    const command = buildModbusCommand();
    
    // Convert to hex string without spaces
    const hexCommand = command.map(byte => byte.toString(16).padStart(2, '0')).join('');
    
    // Send to server
    document.getElementById('modbusResponse').textContent = 'Sending command...';
    document.getElementById('modbusParsedResponse').textContent = 'Waiting for response...';
    
    fetch(`http://localhost:8080/api/modbus_command?command=${hexCommand}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Display the raw response
            const responseHex = data.response.map(byte => 
                byte.toString(16).padStart(2, '0').toUpperCase()).join(' ');
            document.getElementById('modbusResponse').textContent = responseHex;
            
            // Parse and display the formatted response
            parseAndDisplayResponse(data.response);
        })
        .catch(error => {
            console.error('Error sending Modbus command:', error);
            document.getElementById('modbusResponse').textContent = 'Error: ' + error.message;
            document.getElementById('modbusParsedResponse').textContent = 'Failed to get response';
        });
}

// Function to parse and display the response
function parseAndDisplayResponse(response) {
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
            
            // Get the starting register from the command input
            const startRegister = parseInt(document.getElementById('modbusRegisterAddress').value);
            
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