import logging
import os

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "powermeter.log")),
        logging.StreamHandler()
    ]
)

# Power Meter Configuration
CONFIG = {
    # Serial port settings
    'SERIAL_PORT': 'COM3',     # Change this to match your power meter's port
    'BAUD_RATE': 9600,         # Common baud rate for Modbus devices
    'TIMEOUT': 1,              # Timeout in seconds for serial communication
    'MODBUS_ADDRESS': 1,       # Default Modbus device address
    
    # Server settings
    'HTTP_PORT': 8080,         # Port for the HTTP API server
    'WEB_PORT': 8000,          # Port for the web interface
    
    # Operation settings
    'POLL_INTERVAL': 5,        # Seconds between meter readings
    'DETAILED_DATA': True,     # Whether to read detailed (per-phase) data
    'DEFAULT_SCALAR': 3,       # Default scalar based on your meter
    
    # Manual scaling overrides (use these regardless of scalar value from meter)
    'OVERRIDE_SCALING': True,  # Set to False to use scalar from the meter
    'SCALING_FACTORS': {
        'power': 0.1,          # Power scaling factor
        'current': 0.1,        # Current scaling factor
        'voltage': 0.1,        # Voltage scaling factor
        'pf': 0.01,            # Power factor scaling factor
        'frequency': 0.005     # Frequency scaling factor
    },
    
    # Advanced serial settings
    'SERIAL_BYTESIZE': 8,      # 8 data bits
    'SERIAL_PARITY': 'N',      # No parity
    'SERIAL_STOPBITS': 1,      # 1 stop bit
    'SERIAL_XONXOFF': False,   # No software flow control
    'SERIAL_RTSCTS': False,    # No hardware (RTS/CTS) flow control
    'SERIAL_DSRDTR': False,    # No hardware (DSR/DTR) flow control
    
    # Modbus settings
    'MODBUS_TIMEOUT': 1,       # Timeout for Modbus operations
    'MODBUS_RETRIES': 3,       # Number of retries for failed Modbus operations
}