document.addEventListener('DOMContentLoaded', () => {
    setupLoginForm();
});

function setupLoginForm() {
    const form = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        // Hide previous error
        errorMessage.style.display = 'none';
        errorMessage.classList.remove('show');
        
        try {
            console.log('Attempting login...');
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const error = await response.json();
                console.error('Login failed:', error);
                throw new Error(error.detail || 'Login failed');
            }
            
            const result = await response.json();
            console.log('Login successful:', result);
            
            // Login successful, redirect to settings or dashboard
            // Use the same path prefix detection as constants.js
            const pathPrefix = window.location.pathname.startsWith('/cooling-monitor') ? '/cooling-monitor' : '';
            const returnUrl = new URLSearchParams(window.location.search).get('return') || `${pathPrefix}/settings`;
            console.log('Redirecting to:', returnUrl);
            
            // Use setTimeout to ensure cookie is set before redirect
            setTimeout(() => {
                window.location.replace(returnUrl);
            }, 100);
            
        } catch (error) {
            console.error('Login error:', error);
            errorMessage.textContent = error.message || 'Login failed. Please check your credentials.';
            errorMessage.classList.add('show');
            errorMessage.style.display = 'block';
        }
    });
}
