/**
 * UI initialization and event handling
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