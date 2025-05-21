"""
Register definitions and constants for power meter
"""

# Common register addresses
REGISTERS = {
    # System total values
    'ENERGY_KWH_LSW': 44001,
    'ENERGY_KWH_MSW': 44002,
    'POWER_KW': 44003,
    'DEMAND_KW_MAX': 44004,
    'DEMAND_KW_NOW': 44005,
    'POWER_KW_MAX': 44006,
    'POWER_KW_MIN': 44007,
    'REACTIVE_ENERGY_KVARH_LSW': 44008,
    'REACTIVE_ENERGY_KVARH_MSW': 44009,
    'REACTIVE_POWER_KVAR': 44010,
    'APPARENT_ENERGY_KVAH_LSW': 44011,
    'APPARENT_ENERGY_KVAH_MSW': 44012,
    'APPARENT_POWER_KVA': 44013,
    'DISPLACEMENT_PF': 44014,
    'APPARENT_PF': 44015,
    'CURRENT_AVG': 44016,
    'VOLTAGE_LL_AVG': 44017,
    'VOLTAGE_LN_AVG': 44018,
    
    # Phase-to-phase voltages
    'VOLTAGE_L1_L2': 44019,
    'VOLTAGE_L2_L3': 44020,
    'VOLTAGE_L1_L3': 44021,
    'FREQUENCY': 44022,
    
    # Phase 1 values
    'ENERGY_KWH_L1_LSW': 44023,
    'ENERGY_KWH_L1_MSW': 44024,
    
    # Phase 2 values
    'ENERGY_KWH_L2_LSW': 44025,
    'ENERGY_KWH_L2_MSW': 44026,
    
    # Phase 3 values
    'ENERGY_KWH_L3_LSW': 44027,
    'ENERGY_KWH_L3_MSW': 44028,
    
    # Configuration registers
    'DATA_SCALAR': 44602,
    'DEMAND_WINDOW_SIZE': 44603
}

# Register groupings for common operations
REGISTER_GROUPS = {
    'BASIC': [
        REGISTERS['POWER_KW'],
        REGISTERS['CURRENT_AVG'],
        REGISTERS['VOLTAGE_LL_AVG'],
        REGISTERS['VOLTAGE_LN_AVG'],
        REGISTERS['FREQUENCY'],
        REGISTERS['DISPLACEMENT_PF']
    ],
    'ENERGY': [
        REGISTERS['ENERGY_KWH_LSW'],
        REGISTERS['ENERGY_KWH_MSW'],
        REGISTERS['REACTIVE_ENERGY_KVARH_LSW'],
        REGISTERS['REACTIVE_ENERGY_KVARH_MSW'],
        REGISTERS['APPARENT_ENERGY_KVAH_LSW'],
        REGISTERS['APPARENT_ENERGY_KVAH_MSW']
    ],
    'POWER': [
        REGISTERS['POWER_KW'],
        REGISTERS['REACTIVE_POWER_KVAR'],
        REGISTERS['APPARENT_POWER_KVA']
    ],
    'SYSTEM': list(range(44001, 44023)),  # All system registers
    'PHASE_1': list(range(44023, 44031)),  # All phase 1 registers
    'PHASE_2': list(range(44031, 44040)),  # All phase 2 registers
    'PHASE_3': list(range(44040, 44050))   # All phase 3 registers
}

def get_register_name(register_address):
    """Get the name of a register by its address"""
    for name, address in REGISTERS.items():
        if address == register_address:
            return name
    return f"UNKNOWN_{register_address}"

def get_register_group(group_name):
    """Get a list of registers in a group by name"""
    return REGISTER_GROUPS.get(group_name.upper(), [])