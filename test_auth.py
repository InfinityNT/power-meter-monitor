"""
Test script for authentication system
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.auth import AuthenticationManager, User, Session

def test_authentication():
    """Test the authentication system"""
    
    print("Testing Power Meter Authentication System")
    print("=" * 50)
    
    # Create auth manager
    auth_manager = AuthenticationManager()
    
    # Test 1: List default users
    print("\n1. Default users:")
    for username, user in auth_manager.users.items():
        print(f"   - {username}: {user.role} ({', '.join(user.permissions)})")
    
    # Test 2: Authentication
    print("\n2. Testing authentication:")
    
    # Valid login
    result = auth_manager.authenticate('admin', 'admin')
    if result:
        print(f"   ✓ Admin login successful. Token: {result['token'][:16]}...")
        admin_token = result['token']
    else:
        print("   ✗ Admin login failed")
        return
    
    # Invalid login
    result = auth_manager.authenticate('admin', 'wrongpassword')
    if result:
        print("   ✗ Invalid password accepted (should fail)")
    else:
        print("   ✓ Invalid password correctly rejected")
    
    # Test 3: Session validation
    print("\n3. Testing session validation:")
    
    session = auth_manager.validate_session(admin_token)
    if session:
        print(f"   ✓ Session valid for user: {session.user.username}")
    else:
        print("   ✗ Session validation failed")
    
    # Test 4: Permission checking
    print("\n4. Testing permissions:")
    
    permissions_to_test = ['read', 'write', 'admin', 'invalid']
    for permission in permissions_to_test:
        has_permission = auth_manager.check_permission(admin_token, permission)
        status = "✓" if has_permission else "✗"
        print(f"   {status} Admin has '{permission}' permission: {has_permission}")
    
    # Test 5: Add custom user
    print("\n5. Testing user management:")
    
    success = auth_manager.add_user(
        username='testuser',
        password='testpass',
        role='viewer',
        permissions=['read']
    )
    
    if success:
        print("   ✓ Custom user added successfully")
        
        # Test login with new user
        result = auth_manager.authenticate('testuser', 'testpass')
        if result:
            print(f"   ✓ Custom user login successful")
            test_token = result['token']
            
            # Test limited permissions
            can_read = auth_manager.check_permission(test_token, 'read')
            can_write = auth_manager.check_permission(test_token, 'write')
            
            print(f"   ✓ Read permission: {can_read}")
            print(f"   ✓ Write permission (should be False): {can_write}")
        else:
            print("   ✗ Custom user login failed")
    else:
        print("   ✗ Failed to add custom user")
    
    # Test 6: Logout
    print("\n6. Testing logout:")
    
    logout_success = auth_manager.logout(admin_token)
    if logout_success:
        print("   ✓ Logout successful")
        
        # Try to use invalidated session
        session = auth_manager.validate_session(admin_token)
        if session:
            print("   ✗ Session still valid after logout (should be invalid)")
        else:
            print("   ✓ Session correctly invalidated after logout")
    else:
        print("   ✗ Logout failed")
    
    # Test 7: Session cleanup
    print("\n7. Testing session cleanup:")
    
    active_sessions = auth_manager.get_active_sessions()
    print(f"   Active sessions before cleanup: {len(active_sessions)}")
    
    auth_manager.cleanup_expired_sessions()
    
    active_sessions_after = auth_manager.get_active_sessions()
    print(f"   Active sessions after cleanup: {len(active_sessions_after)}")
    
    print("\n" + "=" * 50)
    print("Authentication system test complete!")

def test_imports():
    """Test that all imports work correctly"""
    
    print("\nTesting imports:")
    print("=" * 30)
    
    try:
        # Test core imports
        from core import AuthenticationManager, PowerMeterReader, PowerMeterDataManager
        print("✓ Core imports successful")
        
        # Test main package imports
        from core.auth import AuthenticationManager as MainAuthManager
        print("✓ Main package imports successful")
        
        # Test API imports
        from api.endpoints import PowerMeterHTTPHandler, require_auth
        print("✓ API imports successful")
        
        print("All imports working correctly!")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Test imports first
    if test_imports():
        # Then test authentication
        test_authentication()
    else:
        print("Fix import issues before testing authentication")