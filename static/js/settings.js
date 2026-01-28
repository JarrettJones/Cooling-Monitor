// Load current credentials on page load
document.addEventListener('DOMContentLoaded', () => {
    checkUserRole();
    loadCurrentCredentials();
    loadSMTPSettings();
    loadMonitoringSetting();
    setupForm();
    setupSMTPForm();
    setupMonitoringForm();
});

// Check user role and display current user
async function checkUserRole() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`);
        if (response.ok) {
            const user = await response.json();
            const currentUserEl = document.getElementById('currentUser');
            if (currentUserEl) {
                currentUserEl.textContent = `👤 ${user.username}`;
            }
            
            // Setup logout
            const logoutBtn = document.getElementById('logoutBtn');
            if (logoutBtn && !logoutBtn.hasAttribute('data-settings-listener')) {
                logoutBtn.addEventListener('click', async () => {
                    await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
                    navigateTo('/login');
                });
                logoutBtn.setAttribute('data-settings-listener', 'true');
            }
        } else {
            navigateTo('/login');
        }
    } catch (error) {
        console.error('Error checking user role:', error);
        navigateTo('/login');
    }
}

async function loadCurrentCredentials() {
    try {
        const response = await fetch(`${API_BASE}/settings/redfish-credentials`);
        if (!response.ok) throw new Error('Failed to load credentials');
        
        const data = await response.json();
        
        const usernameField = document.getElementById('username');
        const lastUpdatedField = document.getElementById('lastUpdated');
        const passwordField = document.getElementById('password');
        const confirmPasswordField = document.getElementById('confirmPassword');
        
        if (usernameField) usernameField.value = data.username;
        
        if (lastUpdatedField) {
            if (data.updated_at) {
                const date = new Date(data.updated_at);
                lastUpdatedField.textContent = date.toLocaleString();
            } else {
                lastUpdatedField.textContent = 'Never';
            }
        }
        
        // Clear password fields
        if (passwordField) passwordField.value = '';
        if (confirmPasswordField) confirmPasswordField.value = '';
        
    } catch (error) {
        console.error('Error loading credentials:', error);
        showMessage('Failed to load current credentials', 'error');
    }
}

function setupForm() {
    const form = document.getElementById('credentialsForm');
    if (!form) {
        console.log('Credentials form not found, skipping setup');
        return;
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        // Validate passwords match
        if (password !== confirmPassword) {
            showMessage('Passwords do not match', 'error');
            return;
        }
        
        // Validate password not empty
        if (!password.trim()) {
            showMessage('Password cannot be empty', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/settings/redfish-credentials`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update credentials');
            }
            
            const result = await response.json();
            showMessage('Credentials updated successfully! Changes will take effect on next poll cycle.', 'success');
            
            // Reload credentials to update last updated time
            setTimeout(() => {
                loadCurrentCredentials();
            }, 1000);
            
        } catch (error) {
            console.error('Error updating credentials:', error);
            showMessage(error.message || 'Failed to update credentials', 'error');
        }
    });
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    if (!messageDiv) {
        console.log('Message div not found:', text);
        return;
    }
    messageDiv.textContent = text;
    messageDiv.style.display = 'block';
    
    if (type === 'success') {
        messageDiv.style.backgroundColor = 'var(--success-color)';
        messageDiv.style.color = 'white';
    } else {
        messageDiv.style.backgroundColor = 'var(--danger-color)';
        messageDiv.style.color = 'white';
    }
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

async function loadSMTPSettings() {
    try {
        const response = await fetch(`${API_BASE}/settings/smtp`);
        if (!response.ok) throw new Error('Failed to load SMTP settings');
        
        const data = await response.json();
        
        // Get all form elements with null checks
        const smtp_enabled = document.getElementById('smtp_enabled');
        const smtp_server = document.getElementById('smtp_server');
        const smtp_port = document.getElementById('smtp_port');
        const smtp_username = document.getElementById('smtp_username');
        const smtp_from_email = document.getElementById('smtp_from_email');
        const smtp_to_emails = document.getElementById('smtp_to_emails');
        const smtp_use_tls = document.getElementById('smtp_use_tls');
        const teams_enabled = document.getElementById('teams_enabled');
        const teams_webhook_url = document.getElementById('teams_webhook_url');
        const pump_flow_critical_threshold = document.getElementById('pump_flow_critical_threshold');
        const smtp_password = document.getElementById('smtp_password');
        const smtpLastUpdated = document.getElementById('smtpLastUpdated');
        
        // Update values only if elements exist
        if (smtp_enabled) smtp_enabled.checked = data.smtp_enabled;
        if (smtp_server) smtp_server.value = data.smtp_server || '';
        if (smtp_port) smtp_port.value = data.smtp_port || 587;
        if (smtp_username) smtp_username.value = data.smtp_username || '';
        if (smtp_from_email) smtp_from_email.value = data.smtp_from_email || '';
        if (smtp_to_emails) smtp_to_emails.value = data.smtp_to_emails ? data.smtp_to_emails.join(', ') : '';
        if (smtp_use_tls) smtp_use_tls.checked = data.smtp_use_tls !== false;
        if (teams_enabled) teams_enabled.checked = data.teams_enabled || false;
        if (teams_webhook_url) teams_webhook_url.value = data.teams_webhook_url || '';
        if (pump_flow_critical_threshold) pump_flow_critical_threshold.value = data.pump_flow_critical_threshold || 10.0;
        
        // Clear password field
        if (smtp_password) smtp_password.value = '';
        
        if (smtpLastUpdated) {
            if (data.updated_at) {
                const date = new Date(data.updated_at);
                smtpLastUpdated.textContent = date.toLocaleString();
            } else {
                smtpLastUpdated.textContent = 'Never';
            }
        }
        
    } catch (error) {
        console.error('Error loading SMTP settings:', error);
        showSMTPMessage('Failed to load SMTP settings', 'error');
    }
}

function setupSMTPForm() {
    const form = document.getElementById('smtpForm');
    
    if (!form) {
        console.log('SMTP form not found, skipping setup');
        return;
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const smtp_to_emails_input = document.getElementById('smtp_to_emails').value;
        const smtp_to_emails = smtp_to_emails_input
            .split(',')
            .map(email => email.trim())
            .filter(email => email.length > 0);
        
        const smtpData = {
            smtp_enabled: document.getElementById('smtp_enabled').checked,
            smtp_server: document.getElementById('smtp_server').value,
            smtp_port: parseInt(document.getElementById('smtp_port').value) || 587,
            smtp_username: document.getElementById('smtp_username').value,
            smtp_password: document.getElementById('smtp_password').value,  // Empty if not changing
            smtp_from_email: document.getElementById('smtp_from_email').value,
            smtp_to_emails: smtp_to_emails,
            smtp_use_tls: document.getElementById('smtp_use_tls').checked,
            teams_enabled: document.getElementById('teams_enabled').checked,
            teams_webhook_url: document.getElementById('teams_webhook_url').value,
            pump_flow_critical_threshold: parseFloat(document.getElementById('pump_flow_critical_threshold').value) || 10.0
        };
        
        try {
            const response = await fetch(`${API_BASE}/settings/smtp`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(smtpData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update SMTP settings');
            }
            //Notification settings updated successfully!
            const result = await response.json();
            showSMTPMessage('Email settings updated successfully! Password is encrypted in database.', 'success');
            
            // Reload settings to update last updated time
            setTimeout(() => {
                loadSMTPSettings();
            }, 1000);
            
        } catch (error) {
            console.error('Error updating SMTP settings:', error);
            showSMTPMessage(error.message || 'Failed to update SMTP settings', 'error');
        }
    });
}

function showSMTPMessage(text, type) {
    const messageDiv = document.getElementById('smtpMessage');
    if (!messageDiv) {
        console.log('SMTP message div not found:', text);
        return;
    }
    messageDiv.textContent = text;
    messageDiv.style.display = 'block';
    
    if (type === 'success') {
        messageDiv.style.backgroundColor = 'var(--success-color)';
        messageDiv.style.color = 'white';
    } else {
        messageDiv.style.backgroundColor = 'var(--danger-color)';
        messageDiv.style.color = 'white';
    }
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}
