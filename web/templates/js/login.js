class LoginManager {
    constructor() {
        this.apiUrl = 'http://localhost:8080/api';
        this.init();
        this.checkSystemStatus();
    }

    init() {
        const form = document.getElementById('loginForm');
        form.addEventListener('submit', (e) => this.handleLogin(e));
        
        // Auto-focus username field
        document.getElementById('username').focus();
        
        // Check if already logged in
        this.checkExistingSession();
    }

    async checkExistingSession() {
        const token = sessionStorage.getItem('powermeter_token');
        if (token) {
            try {
                const response = await fetch(`${this.apiUrl}/auth/validate`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    // Already logged in, redirect
                    window.location.href = 'monitor.html';
                    return;
                }
            } catch (error) {
                // Token invalid, continue with login
                sessionStorage.removeItem('powermeter_token');
                sessionStorage.removeItem('powermeter_user');
                sessionStorage.removeItem('powermeter_role');
            }
        }
    }

    async checkSystemStatus() {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const deviceInfo = document.getElementById('deviceInfo');

        try {
            // Try to connect to the API without auth to check if server is running
            const response = await fetch(`${this.apiUrl}/power`);
            
            if (response.status === 401) {
                // Server is running but requires auth (expected)
                statusDot.className = 'status-dot connected';
                statusText.textContent = 'Server Ready';
                deviceInfo.textContent = 'Power meter API server is running';
            } else if (response.ok) {
                // Server running without auth (development mode?)
                statusDot.className = 'status-dot connected';
                statusText.textContent = 'Server Connected';
                deviceInfo.textContent = 'Power meter server accessible';
            } else {
                throw new Error('Server error');
            }
        } catch (error) {
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Connection Error';
            deviceInfo.textContent = 'Cannot connect to power meter server';
            console.error('System status check failed:', error);
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const errorMessage = document.getElementById('errorMessage');
        const successMessage = document.getElementById('successMessage');
        const loginButton = document.getElementById('loginButton');
        const buttonText = document.getElementById('buttonText');

        if (!username || !password) {
            this.showError('Please enter both username and password');
            return;
        }

        // Hide any previous messages
        errorMessage.style.display = 'none';
        successMessage.style.display = 'none';

        // Show loading state
        loginButton.disabled = true;
        buttonText.textContent = 'Signing in...';

        try {
            const response = await fetch(`${this.apiUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Login successful
                sessionStorage.setItem('powermeter_token', data.token);
                sessionStorage.setItem('powermeter_user', data.user.username);
                sessionStorage.setItem('powermeter_role', data.user.role);
                
                // Show success message
                successMessage.style.display = 'block';
                successMessage.textContent = `Welcome ${data.user.username}! Redirecting...`;
                
                // Redirect after short delay
                setTimeout(() => {
                    window.location.href = 'monitor.html';
                }, 1000);
                
            } else {
                // Login failed
                this.showError(data.error || 'Login failed');
                
                // Reset form
                loginButton.disabled = false;
                buttonText.textContent = 'Sign In';
                
                // Clear password field
                document.getElementById('password').value = '';
                document.getElementById('password').focus();
            }
            
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Network error. Please check your connection.');
            
            // Reset form
            loginButton.disabled = false;
            buttonText.textContent = 'Sign In';
        }
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        
        // Shake animation
        errorMessage.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
            errorMessage.style.animation = '';
        }, 500);
    }
}

// Initialize login manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
});