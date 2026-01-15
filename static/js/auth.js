// Shared authentication functions

// Check user role and show/hide admin links
async function checkUserRole() {
    console.log('checkUserRole() called');
    try {
        const response = await fetch(`${API_BASE}/auth/me`);
        console.log('Auth response status:', response.status);
        if (response.ok) {
            const user = await response.json();
            console.log('User data:', user);
            
            // Show user info and logout button
            const currentUserEl = document.getElementById('currentUser');
            const logoutBtn = document.getElementById('logoutBtn');
            const loginLink = document.getElementById('loginLink');
            
            if (currentUserEl) {
                currentUserEl.textContent = `👤 ${user.username}`;
                currentUserEl.style.display = 'inline';
            }
            
            if (loginLink) {
                loginLink.style.display = 'none';
            }
            
            if (logoutBtn) {
                logoutBtn.style.display = 'inline-block';
            }
            
            console.log('Is admin:', user.is_admin);
            if (user.is_admin) {
                // Show admin links with smooth transition
                const addHeatExchangerLink = document.getElementById('addHeatExchangerLink');
                const usersLink = document.getElementById('usersLink');
                const settingsLink = document.getElementById('settingsLink');
                
                console.log('Found admin links:', {
                    addHeatExchangerLink: !!addHeatExchangerLink,
                    usersLink: !!usersLink,
                    settingsLink: !!settingsLink
                });
                
                if (addHeatExchangerLink) {
                    addHeatExchangerLink.style.display = 'inline-block';
                    addHeatExchangerLink.style.visibility = 'visible';
                    addHeatExchangerLink.style.opacity = '1';
                    addHeatExchangerLink.style.pointerEvents = 'auto';
                    console.log('Updated addHeatExchangerLink styles');
                }
                if (usersLink) {
                    usersLink.style.display = 'inline-block';
                    usersLink.style.visibility = 'visible';
                    usersLink.style.opacity = '1';
                    usersLink.style.pointerEvents = 'auto';
                    console.log('Updated usersLink styles');
                }
                if (settingsLink) {
                    settingsLink.style.display = 'inline-block';
                    settingsLink.style.visibility = 'visible';
                    settingsLink.style.opacity = '1';
                    settingsLink.style.pointerEvents = 'auto';
                    console.log('Updated settingsLink styles');
                }
            } else {
                // Hide admin links for non-admin users
                const addHeatExchangerLink = document.getElementById('addHeatExchangerLink');
                const usersLink = document.getElementById('usersLink');
                const settingsLink = document.getElementById('settingsLink');
                
                if (addHeatExchangerLink) {
                    addHeatExchangerLink.style.visibility = 'hidden';
                    addHeatExchangerLink.style.opacity = '0';
                    setTimeout(() => { addHeatExchangerLink.style.display = 'none'; }, 150);
                }
                if (usersLink) {
                    usersLink.style.visibility = 'hidden';
                    usersLink.style.opacity = '0';
                    setTimeout(() => { usersLink.style.display = 'none'; }, 150);
                }
                if (settingsLink) {
                    settingsLink.style.visibility = 'hidden';
                    settingsLink.style.opacity = '0';
                    setTimeout(() => { settingsLink.style.display = 'none'; }, 150);
                }
            }
            
            // Setup logout button (only once)
            if (logoutBtn && !logoutBtn.hasAttribute('data-listener-added')) {
                logoutBtn.setAttribute('data-listener-added', 'true');
                logoutBtn.addEventListener('click', async () => {
                    try {
                        await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
                        navigateTo('/login');
                    } catch (error) {
                        console.error('Logout error:', error);
                        navigateTo('/login');
                    }
                });
            }
        } else {
            // Not logged in - show login button
            const loginLink = document.getElementById('loginLink');
            const logoutBtn = document.getElementById('logoutBtn');
            const currentUserEl = document.getElementById('currentUser');
            
            if (loginLink) loginLink.style.display = 'inline-block';
            if (logoutBtn) logoutBtn.style.display = 'none';
            if (currentUserEl) currentUserEl.style.display = 'none';
        }
    } catch (error) {
        console.log('Not authenticated or error checking role:', error);
        // Show login button on error
        const loginLink = document.getElementById('loginLink');
        const logoutBtn = document.getElementById('logoutBtn');
        const currentUserEl = document.getElementById('currentUser');
        
        if (loginLink) loginLink.style.display = 'inline-block';
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (currentUserEl) currentUserEl.style.display = 'none';
    }
}

// Initialize auth check on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkUserRole);
} else {
    // DOM is already loaded, execute immediately
    checkUserRole();
}
