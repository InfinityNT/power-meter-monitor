/**
 * Dashboard functionality for updating the UI with power meter data
 */
import { fetchMeterData } from './api.js';

/**
 * Update the dashboard with power meter data
 */
async function updateDashboard() {
    try {
        // Show loading indicator
        document.getElementById('status').textContent = 'Connecting...';
        
        // Fetch the data
        const data = await fetchMeterData();
        
        // Update the UI with the data
        updateUIWithData(data);
        
        // Show all data in the raw data section
        document.getElementById('rawDataContent').textContent = 
            JSON.stringify(data, null, 2);
        
        // Update connection status
        const simMsg = data.simulated ? ' (Simulated Data)' : '';
        document.getElementById('status').textContent = 'Connected' + simMsg;
    } catch (error) {
        console.error('Error updating dashboard:', error);
        document.getElementById('status').textContent = 'Error connecting to API';
    }
}

/**
 * Update the UI with power meter data
 * @param {Object} data - Power meter data
 */
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

/**
 * Format a numeric value for display
 * @param {Number} value - Value to format
 * @returns {String} Formatted value
 */
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

// Export functions for use in other modules
export { updateDashboard, updateUIWithData, formatValue };