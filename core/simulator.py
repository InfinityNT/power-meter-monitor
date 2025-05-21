"""
Power meter simulator for testing without hardware
"""
import random
import time
import logging
import math

logger = logging.getLogger('powermeter.core.simulator')

class PowerMeterSimulator:
    """Simulator that generates fake power meter data for testing"""
    
    def __init__(self):
        """Initialize the simulator"""
        self.connected = False
        self._energy_kwh = 1000000  # Starting energy value
        self._last_timestamp = time.time()
        self.device_address = 1  # Default Modbus device address
        
    def connect(self):
        """Simulate connecting to a power meter"""
        self.connected = True
        logger.info("Connected to simulated power meter")
        return True
        
    def disconnect(self):
        """Simulate disconnecting from a power meter"""
        self.connected = False
        logger.info("Disconnected from simulated power meter")
    
    def read_register(self, register_address):
        """
        Simulate reading a single register
        
        Parameters:
        - register_address: Register address to read
        
        Returns:
        - Simulated register value
        """
        # Generate appropriate values for common registers
        if register_address == 44602:  # Data Scalar
            return 3  # Default scalar value
        elif register_address == 44022:  # Frequency
            return 6000  # 60.00 Hz with scalar 3 multiplier
        elif register_address >= 44001 and register_address <= 44020:
            return random.randint(1000, 9000)  # Random value for most registers
        else:
            return random.randint(0, 65535)  # Random value for unknown registers
    
    def read_registers(self, register_address, register_count):
        """
        Simulate reading multiple registers
        
        Parameters:
        - register_address: Starting register address
        - register_count: Number of registers to read
        
        Returns:
        - List of simulated register values
        """
        return [self.read_register(register_address + i) for i in range(register_count)]
    
    def read_data_scalar(self):
        """
        Simulate reading the data scalar register
        
        Returns:
        - Simulated scalar value
        """
        return 3  # Default scalar value
    
    def _get_simulated_values(self):
        """
        Generate a set of realistic simulated values
        
        Returns:
        - Dictionary of simulated values
        """
        from config.settings import CONFIG
        
        # Get current timestamp
        current_time = time.time()
        
        # Generate realistic base values based on the ViewPoint screenshot
        voltage_ln_base = 265  # Line-neutral voltage (V)
        current_base = random.uniform(650, 660)  # Current (A)
        pf_base = 0.99  # Power factor
        frequency = 60 + random.uniform(-0.1, 0.1)  # Frequency (Hz)
        
        # Calculate derived values for system
        voltage_ll_base = voltage_ln_base * math.sqrt(3)  # Line-line voltage (V)
        
        # Generate per-phase values with slight variations
        phase_variations = [
            random.uniform(0.98, 1.02),
            random.uniform(0.97, 1.03),
            random.uniform(0.96, 1.04)
        ]
        
        # Calculate phase values to match ViewPoint values
        phases = []
        for i in range(3):
            var = phase_variations[i]
            voltage_ln = voltage_ln_base * var
            current = current_base * var
            pf = 0.99  # Fixed PF for simulation
            
            # Calculate power values - targeting around 172-174 kW
            power_kw = 173 * var
            apparent_power_kva = power_kw / pf
            reactive_power_kvar = math.sqrt(apparent_power_kva**2 - power_kw**2)
            
            phases.append({
                'voltage_ln': round(voltage_ln, 1),
                'current': round(current, 2),
                'power_kw': round(power_kw, 2),
                'apparent_power_kva': round(apparent_power_kva, 2),
                'reactive_power_kvar': round(reactive_power_kvar, 2),
                'displacement_pf': pf,
                'apparent_pf': pf
            })
        
        # Calculate system totals
        system_power_kw = sum(phase['power_kw'] for phase in phases)
        system_apparent_power_kva = sum(phase['apparent_power_kva'] for phase in phases)
        system_reactive_power_kvar = sum(phase['reactive_power_kvar'] for phase in phases)
        system_current_avg = sum(phase['current'] for phase in phases) / 3
        
        # System power factor
        system_pf = 0.99
            
        # Update energy based on power and time elapsed
        time_diff_hours = (current_time - self._last_timestamp) / 3600
        energy_increment = system_power_kw * time_diff_hours
        self._energy_kwh += energy_increment
        self._last_timestamp = current_time
        
        # Voltage averages
        voltage_ln_avg = sum(phase['voltage_ln'] for phase in phases) / 3
        voltage_ll_avg = voltage_ln_avg * math.sqrt(3)
        
        # Convert real values to raw register values for simulation
        # Using the scaling factors from the config
        scaling = CONFIG.get('SCALING_FACTORS', {
            'power': 0.1,
            'current': 0.1,
            'voltage': 0.1,
            'pf': 0.01,
            'frequency': 0.005
        })
        
        # Calculate raw values
        raw_frequency = int(frequency / scaling['frequency'])
        raw_voltage_ll = int(voltage_ll_avg / scaling['voltage'])
        raw_voltage_ln = int(voltage_ln_avg / scaling['voltage'])
        raw_current = int(system_current_avg / scaling['current'])
        raw_power = int(system_power_kw / scaling['power'])
        raw_pf = int(system_pf / scaling['pf'])
        
        return {
            'phases': phases,
            'system_power_kw': system_power_kw,
            'system_apparent_power_kva': system_apparent_power_kva,
            'system_reactive_power_kvar': system_reactive_power_kvar,
            'system_current_avg': system_current_avg,
            'system_pf': system_pf,
            'voltage_ln_avg': voltage_ln_avg,
            'voltage_ll_avg': voltage_ll_avg,
            'frequency': frequency,
            'raw_frequency': raw_frequency,
            'raw_voltage_ll': raw_voltage_ll,
            'raw_voltage_ln': raw_voltage_ln,
            'raw_current': raw_current,
            'raw_power': raw_power,
            'raw_pf': raw_pf
        }
    
    def read_basic_data(self):
        """
        Simulate reading basic meter data
        
        Returns:
        - Dictionary of simulated basic meter data
        """
        if not self.connected:
            self.connect()
            
        # Generate simulated values
        vals = self._get_simulated_values()
        
        # Return simulated data
        return {
            'timestamp': time.time(),
            'energy_kwh': self._energy_kwh,
            'power_kw': vals['system_power_kw'],
            'reactive_power_kvar': vals['system_reactive_power_kvar'],
            'apparent_power_kva': vals['system_apparent_power_kva'],
            'power_factor': vals['system_pf'],
            'current_avg': vals['system_current_avg'],
            'voltage_ll_avg': vals['voltage_ll_avg'],
            'voltage_ln_avg': vals['voltage_ln_avg'],
            'frequency': vals['frequency'],
            'data_scalar': 3,
            'raw_values': {
                'frequency': vals['raw_frequency'],
                'voltage_ll': vals['raw_voltage_ll'],
                'voltage_ln': vals['raw_voltage_ln'],
                'current': vals['raw_current'],
                'power': vals['raw_power'],
                'pf': vals['raw_pf']
            },
            'multipliers': {
                'power': 0.1,
                'current': 0.1,
                'voltage': 0.1,
                'pf': 0.01,
                'frequency': 0.005
            },
            'simulated': True
        }
    
    def read_detailed_data(self):
        """
        Simulate reading detailed meter data
        
        Returns:
        - Dictionary of simulated detailed meter data
        """
        if not self.connected:
            self.connect()
            
        # Generate simulated values
        vals = self._get_simulated_values()
        phases = vals['phases']
        
        # Return simulated data
        return {
            'timestamp': time.time(),
            'data_scalar': 3,
            'multipliers': {
                'power': 0.1,
                'current': 0.1,
                'voltage': 0.1,
                'pf': 0.01,
                'frequency': 0.005
            },
            'system': {
                'energy_kwh': self._energy_kwh,
                'power_kw': vals['system_power_kw'],
                'demand_kw_max': vals['system_power_kw'] * 1.2,
                'demand_kw_now': vals['system_power_kw'],
                'power_kw_max': vals['system_power_kw'] * 1.3,
                'power_kw_min': vals['system_power_kw'] * 0.7,
                'reactive_energy_kvarh': self._energy_kwh * 0.15,
                'reactive_power_kvar': vals['system_reactive_power_kvar'],
                'apparent_energy_kvah': self._energy_kwh * 1.01,
                'apparent_power_kva': vals['system_apparent_power_kva'],
                'displacement_pf': vals['system_pf'],
                'apparent_pf': vals['system_pf'],
                'current_avg': vals['system_current_avg'],
                'voltage_ll_avg': vals['voltage_ll_avg'],
                'voltage_ln_avg': vals['voltage_ln_avg']
            },
            'voltages': {
                'l1_l2': vals['voltage_ll_avg'] * 0.99,
                'l2_l3': vals['voltage_ll_avg'] * 1.01,
                'l1_l3': vals['voltage_ll_avg']
            },
            'frequency': vals['frequency'],
            'raw_values': {
                'frequency': vals['raw_frequency'],
                'voltage_ll_avg': vals['raw_voltage_ll'],
                'voltage_ln_avg': vals['raw_voltage_ln'],
                'current_avg': vals['raw_current'],
                'power': vals['raw_power'],
                'pf': vals['raw_pf'],
                'data_scalar': 3
            },
            'phase_1': {
                'energy_kwh': self._energy_kwh / 3,
                'power_kw': phases[0]['power_kw'],
                'reactive_energy_kvarh': self._energy_kwh * 0.15 / 3,
                'reactive_power_kvar': phases[0]['reactive_power_kvar'],
                'apparent_energy_kvah': self._energy_kwh * 1.01 / 3,
                'apparent_power_kva': phases[0]['apparent_power_kva'],
                'displacement_pf': phases[0]['displacement_pf'],
                'apparent_pf': phases[0]['apparent_pf'],
                'current': phases[0]['current'],
                'voltage_ln': phases[0]['voltage_ln']
            },
            'phase_2': {
                'energy_kwh': self._energy_kwh / 3,
                'power_kw': phases[1]['power_kw'],
                'reactive_energy_kvarh': self._energy_kwh * 0.15 / 3,
                'reactive_power_kvar': phases[1]['reactive_power_kvar'],
                'apparent_energy_kvah': self._energy_kwh * 1.01 / 3,
                'apparent_power_kva': phases[1]['apparent_power_kva'],
                'displacement_pf': phases[1]['displacement_pf'],
                'apparent_pf': phases[1]['apparent_pf'],
                'current': phases[1]['current'],
                'voltage_ln': phases[1]['voltage_ln']
            },
            'phase_3': {
                'energy_kwh': self._energy_kwh / 3,
                'power_kw': phases[2]['power_kw'],
                'reactive_energy_kvarh': self._energy_kwh * 0.15 / 3,
                'reactive_power_kvar': phases[2]['reactive_power_kvar'],
                'apparent_energy_kvah': self._energy_kwh * 1.01 / 3,
                'apparent_power_kva': phases[2]['apparent_power_kva'],
                'displacement_pf': phases[2]['displacement_pf'],
                'apparent_pf': phases[2]['apparent_pf'],
                'current': phases[2]['current'],
                'voltage_ln': phases[2]['voltage_ln']
            },
            'time_since_reset': int(time.time() % 100000),
            'data_tick_counter': int(time.time() % 60),
            'simulated': True
        }
        
    def read_data(self):
        """
        Convenience method that calls read_basic_data or read_detailed_data
        based on configuration
        
        Returns:
        - Dictionary of simulated meter data
        """
        from config.settings import CONFIG
        
        # Use detailed data if configured, otherwise use basic data
        if CONFIG.get('DETAILED_DATA', False):
            return self.read_detailed_data()
        else:
            return self.read_basic_data()
    
    def test_connection(self):
        """
        Simulate testing the connection
        
        Returns:
        - Always True for simulator
        """
        return self.connect()