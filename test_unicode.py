"""
Unicode-safe test script to verify no encoding issues
Save as: test_unicode_safe.py
"""

import sys
import os
import logging

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging to handle Unicode properly
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('test_unicode')

def test_authentication_messages():
    """Test that all authentication messages work without Unicode errors"""
    
    print("Testing Power Monitor Authentication System")
    print("=" * 50)
    
    try:
        from core.auth import AuthenticationManager
        
        # Test authentication manager
        auth_manager = AuthenticationManager()
        logger.info("Authentication system initialized successfully")
        logger.info("Available users: {}".format(list(auth_manager.users.keys())))
        
        # Test user login
        result = auth_manager.authenticate('admin', 'admin')
        if result:
            logger.info("Admin authentication successful")
            logger.info("User role: {}".format(result['user']['role']))
            logger.info("Permissions: {}".format(", ".join(result['user']['permissions'])))
        else:
            logger.error("Admin authentication failed")
            
        # Test various log messages that were causing issues
        logger.info("Authentication required - System available at http://localhost:8000/login.html")
        logger.info("Default users available:")
        logger.info("   * admin/admin (full access)")
        logger.info("   * operator/operator (read/write)")
        logger.info("   * viewer/viewer (read only)")
        logger.info("Data is simulated for testing purposes")
        
        print("\nAll Unicode-safe messages logged successfully!")
        return True
        
    except UnicodeEncodeError as e:
        print(f"Unicode encoding error: {e}")
        return False
    except Exception as e:
        print(f"Other error: {e}")
        return False

def test_system_startup():
    """Test system startup messages"""
    
    try:
        logger.info("Starting power meter monitoring application")
        logger.info("Testing connection to power meter...")
        logger.info("Power meter connection test successful!")
        logger.info("System running. HTTP API available at http://localhost:8080/")
        logger.info("Press Ctrl+C to exit.")
        
        print("System startup messages work correctly!")
        return True
        
    except UnicodeEncodeError as e:
        print(f"Unicode encoding error in startup: {e}")
        return False

if __name__ == "__main__":
    print("Testing Unicode-safe logging...")
    
    auth_test = test_authentication_messages()
    startup_test = test_system_startup()
    
    if auth_test and startup_test:
        print("\nSUCCESS: All tests passed - no Unicode encoding issues!")
        sys.exit(0)
    else:
        print("\nFAILED: Unicode encoding issues found")
        sys.exit(1)