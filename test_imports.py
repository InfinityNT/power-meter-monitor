"""
Simple test to verify imports work
Save as: test_imports.py
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_step_by_step():
    """Test imports step by step"""
    
    print("Testing Power Meter System Imports")
    print("=" * 40)
    
    # Step 1: Test basic core imports
    print("\n1. Testing basic core imports...")
    try:
        from core import PowerMeterDataManager, PowerMeterReader, PowerMeterSimulator
        print("   ✓ Basic core imports successful")
    except ImportError as e:
        print(f"   ✗ Basic core imports failed: {e}")
        return False
    
    # Step 2: Test auth imports
    print("\n2. Testing auth imports...")
    try:
        from core.auth import User, Session, AuthenticationManager
        print("   ✓ Auth imports successful")
    except ImportError as e:
        print(f"   ✗ Auth imports failed: {e}")
        print("   Make sure you created core/auth.py file")
        return False
    
    # Step 3: Test auth import from core
    print("\n3. Testing auth import from core package...")
    try:
        from core import User, Session, AuthenticationManager
        print("   ✓ Auth imports from core package successful")
    except ImportError as e:
        print(f"   ✗ Auth imports from core package failed: {e}")
        print("   Update your core/__init__.py file")
        return False
    
    # Step 4: Test basic functionality
    print("\n4. Testing basic auth functionality...")
    try:
        auth_manager = AuthenticationManager()
        print(f"   ✓ AuthenticationManager created with {len(auth_manager.users)} users")
        
        # Test authentication
        result = auth_manager.authenticate('admin', 'admin')
        if result:
            print("   ✓ Admin authentication successful")
        else:
            print("   ✗ Admin authentication failed")
            return False
            
    except Exception as e:
        print(f"   ✗ Auth functionality failed: {e}")
        return False
    
    # Step 5: Test API imports
    print("\n5. Testing API imports...")
    try:
        from api.endpoints import PowerMeterHTTPHandler
        print("   ✓ API imports successful")
    except ImportError as e:
        print(f"   ✗ API imports failed: {e}")
        print("   Update your api/endpoints.py file")
        return False
    
    print("\n" + "=" * 40)
    print("✓ All imports working correctly!")
    
    return True

if __name__ == "__main__":
    success = test_step_by_step()
    
    if success:
        print("\n🎉 Your authentication system is ready to use!")
    else:
        print("\n❌ Please fix the import issues above before proceeding.")
    
    sys.exit(0 if success else 1)