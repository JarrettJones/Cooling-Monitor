// Monitoring control functions

// Setup monitoring form
function setupMonitoringForm() {
    document.getElementById('monitoringForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveMonitoringSetting();
    });
}

// Load current monitoring setting
async function loadMonitoringSetting() {
    try {
        const response = await fetch(`${API_BASE}/settings/monitoring`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('monitoring_enabled').checked = data.monitoring_enabled;
            document.getElementById('monitoring_polling_interval').value = data.polling_interval_seconds || 30;
        }
    } catch (error) {
        console.error('Error loading monitoring setting:', error);
    }
}

// Save monitoring setting
async function saveMonitoringSetting() {
    const enabled = document.getElementById('monitoring_enabled').checked;
    const pollingInterval = parseInt(document.getElementById('monitoring_polling_interval').value) || 30;
    
    try {
        const response = await fetch(`${API_BASE}/settings/monitoring`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                monitoring_enabled: enabled,
                polling_interval_seconds: pollingInterval
            })
        });
        
        if (response.ok) {
            showMonitoringMessage(`Monitoring settings updated successfully! Polling interval: ${pollingInterval}s`, 'success');
        } else {
            const error = await response.json();
            showMonitoringMessage(error.detail || 'Failed to update monitoring settings', 'error');
        }
    } catch (error) {
        showMonitoringMessage('Error updating monitoring settings', 'error');
        console.error('Error:', error);
    }
}

// Show monitoring message
function showMonitoringMessage(text, type) {
    const messageDiv = document.getElementById('monitoring-message');
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
