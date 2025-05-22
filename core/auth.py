"""
Authentication manager for Power Meter monitoring system
Save as: core/auth.py
"""
import hashlib
import secrets
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger('powermeter.core.auth')

class User:
    """User class for authentication"""
    
    def __init__(self, username: str, password_hash: str, role: str, permissions: list):
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.permissions = permissions
        self.created_at = datetime.now()
        self.last_login = None
    
    def check_password(self, password: str, salt: str) -> bool:
        """Check if provided password matches user's password"""
        test_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return test_hash == self.password_hash
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (without password)"""
        return {
            'username': self.username,
            'role': self.role,
            'permissions': self.permissions,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Session:
    """Session class for managing user sessions"""
    
    def __init__(self, user: User, token: str, expires_in_hours: int = 8):
        self.user = user
        self.token = token
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=expires_in_hours)
        self.last_accessed = datetime.now()
    
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        return datetime.now() < self.expires_at
    
    def refresh(self):
        """Refresh session last accessed time"""
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert session to dictionary"""
        return {
            'token': self.token,
            'user': self.user.to_dict(),
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat()
        }

class AuthenticationManager:
    """Main authentication manager"""
    
    def __init__(self):
        self.salt = "powermeter_salt_2024"  # In production, use environment variable
        self.users = {}
        self.sessions = {}
        self._init_default_users()
    
    def _init_default_users(self):
        """Initialize default users"""
        default_users = [
            {
                'username': 'admin',
                'password': 'admin',
                'role': 'admin',
                'permissions': ['read', 'write', 'admin', 'config', 'modbus']
            },
            {
                'username': 'operator',
                'password': 'operator', 
                'role': 'operator',
                'permissions': ['read', 'write', 'modbus']
            },
            {
                'username': 'viewer',
                'password': 'viewer',
                'role': 'viewer',
                'permissions': ['read']
            }
        ]
        
        for user_data in default_users:
            password_hash = self._hash_password(user_data['password'])
            user = User(
                username=user_data['username'],
                password_hash=password_hash,
                role=user_data['role'],
                permissions=user_data['permissions']
            )
            self.users[user_data['username']] = user
            
        logger.info(f"Initialized {len(self.users)} default users")
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        return hashlib.sha256(f"{password}{self.salt}".encode()).hexdigest()
    
    def _generate_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_hex(32)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user credentials
        
        Parameters:
        - username: Username
        - password: Password
        
        Returns:
        - Dictionary with session info if successful, None otherwise
        """
        if username not in self.users:
            logger.warning(f"Authentication failed: user '{username}' not found")
            return None
        
        user = self.users[username]
        
        if not user.check_password(password, self.salt):
            logger.warning(f"Authentication failed: invalid password for user '{username}'")
            return None
        
        # Create session
        token = self._generate_token()
        session = Session(user, token)
        self.sessions[token] = session
        
        # Update user last login
        user.last_login = datetime.now()
        
        logger.info(f"User '{username}' authenticated successfully")
        
        return {
            'token': token,
            'user': user.to_dict(),
            'expires_at': session.expires_at.isoformat()
        }
    
    def validate_session(self, token: str) -> Optional[Session]:
        """
        Validate session token
        
        Parameters:
        - token: Session token
        
        Returns:
        - Session object if valid, None otherwise
        """
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        
        if not session.is_valid():
            # Remove expired session
            del self.sessions[token]
            logger.debug(f"Session {token[:8]}... expired and removed")
            return None
        
        # Refresh session
        session.refresh()
        return session
    
    def logout(self, token: str) -> bool:
        """
        Logout and invalidate session
        
        Parameters:
        - token: Session token to invalidate
        
        Returns:
        - True if session was found and removed, False otherwise
        """
        if token in self.sessions:
            username = self.sessions[token].user.username
            del self.sessions[token]
            logger.info(f"User '{username}' logged out")
            return True
        return False
    
    def check_permission(self, token: str, required_permission: str) -> bool:
        """
        Check if user has required permission
        
        Parameters:
        - token: Session token
        - required_permission: Permission to check
        
        Returns:
        - True if user has permission, False otherwise
        """
        session = self.validate_session(token)
        if not session:
            return False
        
        return session.user.has_permission(required_permission)
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user object from session token
        
        Parameters:
        - token: Session token
        
        Returns:
        - User object if valid session, None otherwise
        """
        session = self.validate_session(token)
        return session.user if session else None
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_tokens = []
        for token, session in self.sessions.items():
            if not session.is_valid():
                expired_tokens.append(token)
        
        for token in expired_tokens:
            username = self.sessions[token].user.username
            del self.sessions[token]
            logger.debug(f"Removed expired session for user '{username}'")
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")
    
    def get_active_sessions(self) -> Dict[str, Dict]:
        """Get information about active sessions"""
        active_sessions = {}
        for token, session in self.sessions.items():
            if session.is_valid():
                active_sessions[token] = session.to_dict()
        return active_sessions
    
    def add_user(self, username: str, password: str, role: str, permissions: list) -> bool:
        """
        Add a new user
        
        Parameters:
        - username: Username
        - password: Password
        - role: User role
        - permissions: List of permissions
        
        Returns:
        - True if user added successfully, False if user already exists
        """
        if username in self.users:
            logger.warning(f"Cannot add user '{username}': already exists")
            return False
        
        password_hash = self._hash_password(password)
        user = User(username, password_hash, role, permissions)
        self.users[username] = user
        
        logger.info(f"Added new user '{username}' with role '{role}'")
        return True
    
    def remove_user(self, username: str) -> bool:
        """
        Remove a user
        
        Parameters:
        - username: Username to remove
        
        Returns:
        - True if user removed successfully, False if user not found
        """
        if username not in self.users:
            logger.warning(f"Cannot remove user '{username}': not found")
            return False
        
        # Remove user sessions
        tokens_to_remove = []
        for token, session in self.sessions.items():
            if session.user.username == username:
                tokens_to_remove.append(token)
        
        for token in tokens_to_remove:
            del self.sessions[token]
        
        # Remove user
        del self.users[username]
        
        logger.info(f"Removed user '{username}' and {len(tokens_to_remove)} active sessions")
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Parameters:
        - username: Username
        - old_password: Current password
        - new_password: New password
        
        Returns:
        - True if password changed successfully, False otherwise
        """
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        if not user.check_password(old_password, self.salt):
            logger.warning(f"Password change failed for '{username}': invalid old password")
            return False
        
        # Update password
        user.password_hash = self._hash_password(new_password)
        
        logger.info(f"Password changed for user '{username}'")
        return True