// Shared navbar functionality for all pages
// API_BASE is defined in constants.js

// Update alert badge with count
async function updateAlertBadge() {
    try {
        const response = await fetch(`${API_BASE}/alerts/count?acknowledged=false&resolved=false`);
        if (response.ok) {
            const data = await response.json();
            const badge = document.getElementById('alertBadge');
            const navLink = document.getElementById('alertsNavLink');
            
            if (badge && navLink) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline-block';
                    navLink.style.color = 'var(--danger-color)';
                } else {
                    badge.style.display = 'none';
                    navLink.style.color = '';
                }
            }
        }
    } catch (error) {
        console.error('Error fetching alert count:', error);
    }
}

// Initialize navbar on page load
document.addEventListener('DOMContentLoaded', () => {
    // Update alert badge immediately
    updateAlertBadge();
    
    // Update alert badge every 30 seconds
    setInterval(updateAlertBadge, 30000);
});
