// API Base URL
const API_BASE = '/api';

// Current filters
let currentFilters = {
    status: 'active',
    heatExchanger: 'all',
    severity: 'all'
};

// WebSocket connection
let ws = null;

// Load alerts on page load
document.addEventListener('DOMContentLoaded', () => {
    checkUserRole();
    loadHeatExchangers();
    loadAlerts();
    setupFilters();
    connectWebSocket();
    
    // Refresh every 30 seconds
    setInterval(loadAlerts, 30000);
});

// Check user role and display navigation
async function checkUserRole() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            const user = await response.json();
            
            // Show user info and logout
            document.getElementById('currentUser').textContent = `👤 ${user.username}`;
            document.getElementById('currentUser').style.display = 'inline';
            document.getElementById('logoutBtn').style.display = 'inline-block';
            
            if (user.is_admin) {
                // Show admin links
                document.getElementById('addHeatExchangerLink').style.display = 'inline-block';
                document.getElementById('usersLink').style.display = 'inline-block';
                document.getElementById('settingsLink').style.display = 'inline-block';
            }
            
            // Setup logout
            document.getElementById('logoutBtn').addEventListener('click', async () => {
                await fetch('/api/auth/logout', { method: 'POST' });
                window.location.href = '/login';
            });
        } else {
            // Show login button
            document.getElementById('loginLink').style.display = 'inline-block';
        }
    } catch (error) {
        console.log('Not authenticated:', error);
        document.getElementById('loginLink').style.display = 'inline-block';
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_alert') {
            console.log('New alert received via WebSocket:', data);
            loadAlerts(); // Reload alerts
        }
    };
    
    ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...');
        setTimeout(connectWebSocket, 5000);
    };
}

async function loadHeatExchangers() {
    try {
        const response = await fetch(`${API_BASE}/heat-exchangers`);
        const exchangers = await response.json();
        
        const select = document.getElementById('filterHeatExchanger');
        exchangers.forEach(he => {
            const option = document.createElement('option');
            option.value = he.id;
            option.textContent = he.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading heat exchangers:', error);
    }
}

async function loadAlerts() {
    try {
        // Build query parameters
        const params = new URLSearchParams();
        
        if (currentFilters.status === 'active') {
            params.append('acknowledged', 'false');
            params.append('resolved', 'false');
        } else if (currentFilters.status === 'acknowledged') {
            params.append('acknowledged', 'true');
            params.append('resolved', 'false');
        } else if (currentFilters.status === 'resolved') {
            params.append('resolved', 'true');
        }
        
        if (currentFilters.heatExchanger !== 'all') {
            params.append('heat_exchanger_id', currentFilters.heatExchanger);
        }
        
        if (currentFilters.severity !== 'all') {
            params.append('severity', currentFilters.severity);
        }
        
        const response = await fetch(`${API_BASE}/alerts?${params.toString()}`);
        const alerts = await response.json();
        
        // Update stats
        updateStats(alerts);
        
        // Render alerts
        renderAlerts(alerts);
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

async function updateStats(alerts) {
    try {
        // Get counts
        const totalResponse = await fetch(`${API_BASE}/alerts/count`);
        const totalData = await totalResponse.json();
        
        const activeResponse = await fetch(`${API_BASE}/alerts/count?acknowledged=false&resolved=false`);
        const activeData = await activeResponse.json();
        
        const ackResponse = await fetch(`${API_BASE}/alerts/count?acknowledged=true&resolved=false`);
        const ackData = await ackResponse.json();
        
        const resolvedResponse = await fetch(`${API_BASE}/alerts/count?resolved=true`);
        const resolvedData = await resolvedResponse.json();
        
        document.getElementById('totalAlerts').textContent = totalData.count;
        document.getElementById('activeAlerts').textContent = activeData.count;
        document.getElementById('acknowledgedAlerts').textContent = ackData.count;
        document.getElementById('resolvedAlerts').textContent = resolvedData.count;
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

function renderAlerts(alerts) {
    const container = document.getElementById('alertsContainer');
    const noAlerts = document.getElementById('noAlerts');
    
    if (alerts.length === 0) {
        container.innerHTML = '';
        noAlerts.style.display = 'block';
        return;
    }
    
    noAlerts.style.display = 'none';
    container.innerHTML = alerts.map(alert => createAlertCard(alert)).join('');
}

function createAlertCard(alert) {
    const createdDate = new Date(alert.created_at).toLocaleString();
    const ackDate = alert.acknowledged_at ? new Date(alert.acknowledged_at).toLocaleString() : null;
    const resolvedDate = alert.resolved_at ? new Date(alert.resolved_at).toLocaleString() : null;
    
    let statusClass = '';
    if (alert.resolved) statusClass = 'resolved';
    else if (alert.acknowledged) statusClass = 'acknowledged';
    
    let badges = `<span class="badge badge-${alert.severity}">${alert.severity}</span>`;
    if (alert.acknowledged) badges += '<span class="badge badge-acknowledged">Acknowledged</span>';
    if (alert.resolved) badges += '<span class="badge badge-resolved">Resolved</span>';
    
    let actions = '';
    if (!alert.resolved) {
        if (!alert.acknowledged) {
            actions = `
                <button class="btn btn-small" onclick="acknowledgeAlert(${alert.id})">
                    ✓ Acknowledge
                </button>
                <button class="btn btn-small" onclick="resolveAlert(${alert.id})">
                    ✓✓ Resolve
                </button>
            `;
        } else {
            actions = `
                <button class="btn btn-small" onclick="resolveAlert(${alert.id})">
                    ✓✓ Resolve
                </button>
            `;
        }
        actions += `
            <button class="btn btn-small btn-secondary" onclick="toggleCommentForm(${alert.id})">
                💬 Add Comment
            </button>
        `;
    }
    
    let metaInfo = '';
    if (alert.acknowledged_by) {
        metaInfo += `<div>Acknowledged by ${alert.acknowledged_by} on ${ackDate}</div>`;
    }
    if (alert.resolved_by) {
        metaInfo += `<div>Resolved by ${alert.resolved_by} on ${resolvedDate}</div>`;
    }
    
    return `
        <div class="card alert-card ${alert.severity} ${statusClass}">
            <div class="alert-header">
                <div>
                    <h3 class="alert-title">${alert.title}</h3>
                    <div class="alert-meta">
                        <strong>${alert.heat_exchanger_name}</strong> • ${createdDate}
                    </div>
                    ${metaInfo ? `<div class="alert-meta" style="margin-top: 0.5rem;">${metaInfo}</div>` : ''}
                </div>
                <div class="alert-badges">
                    ${badges}
                </div>
            </div>
            
            ${alert.description ? `<p>${alert.description}</p>` : ''}
            
            <div class="alert-details">
                ${alert.pump_name ? `
                    <div class="detail-item">
                        <span class="detail-label">Pump</span>
                        <span class="detail-value">${alert.pump_name}</span>
                    </div>
                ` : ''}
                ${alert.flow_rate !== null ? `
                    <div class="detail-item">
                        <span class="detail-label">Flow Rate</span>
                        <span class="detail-value" style="color: var(--danger-color); font-weight: 600;">
                            ${alert.flow_rate.toFixed(2)} L/min
                        </span>
                    </div>
                ` : ''}
                ${alert.threshold !== null ? `
                    <div class="detail-item">
                        <span class="detail-label">Threshold</span>
                        <span class="detail-value">${alert.threshold.toFixed(2)} L/min</span>
                    </div>
                ` : ''}
            </div>
            
            ${alert.comments ? `
                <div class="alert-comments">
                    <strong>Comments:</strong><br>
                    ${alert.comments}
                </div>
            ` : ''}
            
            <div class="alert-actions">
                ${actions}
            </div>
            
            <div id="commentForm${alert.id}" class="comment-form" style="display: none;">
                <input 
                    type="text" 
                    id="commentInput${alert.id}" 
                    placeholder="Add a comment..."
                    onkeypress="if(event.key==='Enter') addComment(${alert.id})"
                >
                <button class="btn btn-small" onclick="addComment(${alert.id})">Post</button>
                <button class="btn btn-small btn-secondary" onclick="toggleCommentForm(${alert.id})">Cancel</button>
            </div>
        </div>
    `;
}

async function acknowledgeAlert(alertId) {
    try {
        const response = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (!response.ok) throw new Error('Failed to acknowledge alert');
        
        loadAlerts(); // Reload
    } catch (error) {
        console.error('Error acknowledging alert:', error);
        alert('Failed to acknowledge alert');
    }
}

async function resolveAlert(alertId) {
    try {
        const response = await fetch(`${API_BASE}/alerts/${alertId}/resolve`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (!response.ok) throw new Error('Failed to resolve alert');
        
        loadAlerts(); // Reload
    } catch (error) {
        console.error('Error resolving alert:', error);
        alert('Failed to resolve alert');
    }
}

function toggleCommentForm(alertId) {
    const form = document.getElementById(`commentForm${alertId}`);
    form.style.display = form.style.display === 'none' ? 'flex' : 'none';
}

async function addComment(alertId) {
    const input = document.getElementById(`commentInput${alertId}`);
    const comment = input.value.trim();
    
    if (!comment) return;
    
    try {
        const response = await fetch(`${API_BASE}/alerts/${alertId}/comment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comments: comment })
        });
        
        if (!response.ok) throw new Error('Failed to add comment');
        
        input.value = '';
        toggleCommentForm(alertId);
        loadAlerts(); // Reload
    } catch (error) {
        console.error('Error adding comment:', error);
        alert('Failed to add comment');
    }
}

function setupFilters() {
    document.getElementById('filterStatus').addEventListener('change', (e) => {
        currentFilters.status = e.target.value;
        loadAlerts();
    });
    
    document.getElementById('filterHeatExchanger').addEventListener('change', (e) => {
        currentFilters.heatExchanger = e.target.value;
        loadAlerts();
    });
    
    document.getElementById('filterSeverity').addEventListener('change', (e) => {
        currentFilters.severity = e.target.value;
        loadAlerts();
    });
}
