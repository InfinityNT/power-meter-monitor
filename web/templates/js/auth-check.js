/**
 * Authentication check for protected pages
 * Updated to use correct API URLs
 */

class AuthChecker {
    constructor() {
        this.apiUrl = 'http://localhost:8080/api';  // API server port
        this.token = sessionStorage.getItem('powermeter_token');
        this.user = null;
    }

    async checkAuthentication() {
        // If no token, redirect to login
        if (!this.token) {
            this.redirectToLogin();
            return false;
        }

        try {
            // Validate token with server
            const response = await fetch(`${this.apiUrl}/auth/validate`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.user = data.user;
                this.setupAuthenticatedInterface();
                return true;
            } else {
                // Token invalid, clear and redirect
                this.clearAuth();
                this.redirectToLogin();
                return false;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            // Network error - show warning but don't redirect
            this.showNetworkWarning();
            return true; // Allow offline access
        }
    }

    setupAuthenticatedInterface() {
        // Add user header to page
        this.addUserHeader();
        
        // Apply role restrictions
        this.applyRoleRestrictions();
        
        // Setup authenticated fetch
        this.setupAuthenticatedFetch();
    }

    addUserHeader() {
        // Check if header already exists
        if (document.getElementById('authHeader')) return;

        const header = document.createElement('div');
        header.id = 'authHeader';
        header.style.cssText = `
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        `;

        header.innerHTML = `
            <div>
                <h1 style="margin: 0; font-size: 24px;">Power Monitor Dashboard</h1>
                <small style="opacity: 0.8;">Real-time power monitoring system</small>
            </div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background: rgba(255,255,255,0.1); padding: 8px 12px; border-radius: 20px; font-size: 14px;">
                    User: ${this.user.username} (${this.user.role})
                </div>
                <button onclick="authChecker.logout()" style="
                    background: #e74c3c;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background 0.3s ease;
                " onmouseover="this.style.background='#c0392b'" onmouseout="this.style.background='#e74c3c'">
                    Logout
                </button>
            </div>
        `;

        // Insert at the beginning of body
        document.body.insertBefore(header, document.body.firstChild);
    }

    applyRoleRestrictions() {
        const user = this.user;
        
        if (user.role === 'viewer') {
            // Add warning for read-only access
            this.addRoleWarning('You have read-only access. Some features are limited.');
            
            // Disable write operations
            this.disableWriteOperations();
        }
        
        if (user.role !== 'admin') {
            // Hide admin-only features
            this.hideAdminFeatures();
        }
    }

    disableWriteOperations() {
        // Disable Modbus command sending
        const writeButtons = ['sendModbusCommandBtn', 'buildModbusCommandBtn'];
        writeButtons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.disabled = true;
                button.title = 'Read-only access - contact administrator';
                button.style.opacity = '0.5';
            }
        });

        // Disable function code dropdown options for write operations
        const functionSelect = document.getElementById('modbusFunctionCode');
        if (functionSelect) {
            const writeOptions = functionSelect.querySelectorAll('option[value="6"], option[value="16"]');
            writeOptions.forEach(option => {
                option.disabled = true;
                option.textContent += ' (Admin only)';
            });
        }
    }

    hideAdminFeatures() {
        // Hide admin-only sections
        const adminElements = document.querySelectorAll('.admin-only');
        adminElements.forEach(element => {
            element.style.display = 'none';
        });
    }

    addRoleWarning(message) {
        const warning = document.createElement('div');
        warning.style.cssText = `
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 12px 15px;
            border-radius: 6px;
            margin: 10px 0;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        warning.innerHTML = `<span>WARNING:</span><span>${message}</span>`;
        
        // Insert after auth header
        const authHeader = document.getElementById('authHeader');
        if (authHeader) {
            authHeader.parentNode.insertBefore(warning, authHeader.nextSibling);
        }
    }

    showNetworkWarning() {
        const warning = document.createElement('div');
        warning.style.cssText = `
            background: #ffeaa7;
            border: 1px solid #fdcb6e;
            color: #a05624;
            padding: 12px 15px;
            border-radius: 6px;
            margin: 10px 0;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        warning.innerHTML = `<span>WARNING:</span><span>Network connection issue - running in offline mode</span>`;
        
        document.body.insertBefore(warning, document.body.firstChild);
    }

    setupAuthenticatedFetch() {
        // Override global fetch to include auth header
        const originalFetch = window.fetch;
        window.fetch = async (url, options = {}) => {
            // If it's an API call, add authentication
            if (url.includes('/api/') && this.token) {
                options.headers = {
                    ...options.headers,
                    'Authorization': `Bearer ${this.token}`
                };
            }
            
            const response = await originalFetch(url, options);
            
            // Handle auth errors globally
            if (response.status === 401 && url.includes('/api/')) {
                this.clearAuth();
                this.redirectToLogin();
                throw new Error('Authentication required');
            }
            
            return response;
        };
    }

    logout() {
        if (confirm('Are you sure you want to logout?')) {
            // Notify server
            if (this.token) {
                fetch(`${this.apiUrl}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                }).catch(() => {
                    // Ignore errors
                });
            }
            
            this.clearAuth();
            this.redirectToLogin();
        }
    }

    clearAuth() {
        sessionStorage.removeItem('powermeter_token');
        sessionStorage.removeItem('powermeter_user');
        sessionStorage.removeItem('powermeter_role');
        this.token = null;
        this.user = null;
    }

    redirectToLogin() {
        // Redirect to login on the API server port
        window.location.href = 'http://localhost:8080/login.html';
    }
}

// Create global instance
const authChecker = new AuthChecker();

// Auto-check authentication when page loads
document.addEventListener('DOMContentLoaded', async () => {
    const isAuthenticated = await authChecker.checkAuthentication();
    
    if (isAuthenticated) {
        console.log('Authentication verified, user:', authChecker.user);
        
        // Dispatch custom event that monitor page can listen to
        document.dispatchEvent(new CustomEvent('authenticationReady', {
            detail: { user: authChecker.user }
        }));
    }
});

// Export for global access
window.authChecker = authChecker;