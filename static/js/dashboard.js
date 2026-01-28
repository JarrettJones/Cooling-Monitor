// API_BASE is defined in constants.js

// WebSocket connection
let ws = null;
let reconnectInterval = null;

// Data storage
let heatExchangers = [];
let latestData = {};
let currentTypeFilter = 'all';
let currentLocationFilter = 'all';
let isAdmin = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkUserRole();
    fetchHeatExchangers();
    connectWebSocket();
    updateAlertBadge();
    
    // Refresh dashboard data every 10 seconds
    setInterval(fetchHeatExchangers, 10000);
    
    // Update alert badge every 30 seconds
    setInterval(updateAlertBadge, 30000);
    
    // Filter button listeners
    document.getElementById('filterAll').addEventListener('click', () => filterByType('all'));
    document.getElementById('filterCallan').addEventListener('click', () => filterByType('Callan'));
    document.getElementById('filterAtlas').addEventListener('click', () => filterByType('Atlas'));
    document.getElementById('locationFilter').addEventListener('change', (e) => filterByLocation(e.target.value));
});

// Check user role and show/hide admin links
async function checkUserRole() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`);
        if (response.ok) {
            const user = await response.json();
            
            // Show user info and logout button
            document.getElementById('currentUser').textContent = `👤 ${user.username}`;
            document.getElementById('currentUser').style.display = 'inline';
            document.getElementById('loginLink').style.display = 'none';
            document.getElementById('logoutBtn').style.display = 'inline-block';
            
            if (user.is_admin) {
                isAdmin = true;
                // Show admin links
                document.getElementById('addHeatExchangerLink').style.display = 'inline-block';
                document.getElementById('usersLink').style.display = 'inline-block';
                document.getElementById('settingsLink').style.display = 'inline-block';
            }
            
            // Setup logout button
            document.getElementById('logoutBtn').addEventListener('click', async () => {
                try {
                    await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
                    navigateTo('/login');
                } catch (error) {
                    console.error('Logout error:', error);
                    navigateTo('/login');
                }
            });
        } else {
            // Not logged in - show login button
            document.getElementById('loginLink').style.display = 'inline-block';
            document.getElementById('logoutBtn').style.display = 'none';
            document.getElementById('currentUser').style.display = 'none';
        }
    } catch (error) {
        console.log('Not authenticated or error checking role:', error);
        // Show login button on error
        document.getElementById('loginLink').style.display = 'inline-block';
        document.getElementById('logoutBtn').style.display = 'none';
        document.getElementById('currentUser').style.display = 'none';
    }
}

// Fetch all heat exchangers
async function fetchHeatExchangers() {
    try {
        const response = await fetch(`${API_BASE}/heat-exchangers/`);
        heatExchangers = await response.json();
        
        const latestResponse = await fetch(`${API_BASE}/monitoring/latest`);
        const latest = await latestResponse.json();
        
        // Convert array to object
        latestData = {};
        latest.forEach(data => {
            latestData[data.heat_exchanger_id] = data;
        });
        
        // Populate location filter
        populateLocationFilter();
        
        renderHeatExchangers();
    } catch (error) {
        console.error('Error fetching heat exchangers:', error);
        document.getElementById('heat-exchangers-grid').innerHTML = 
            '<div class="error">Failed to load heat exchangers</div>';
    }
}

function filterByType(type) {
    currentTypeFilter = type;
    
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if (type === 'all') {
        document.getElementById('filterAll').classList.add('active');
    } else if (type === 'Callan') {
        document.getElementById('filterCallan').classList.add('active');
    } else if (type === 'Atlas') {
        document.getElementById('filterAtlas').classList.add('active');
    }
    
    renderHeatExchangers();
}

function filterByLocation(location) {
    currentLocationFilter = location;
    renderHeatExchangers();
}

function populateLocationFilter() {
    // Get unique cities from heat exchangers
    const cities = [...new Set(heatExchangers.map(he => he.location.city))].sort();
    
    const select = document.getElementById('locationFilter');
    // Keep "All Locations" option
    select.innerHTML = '<option value="all">All Locations</option>';
    
    // Add city options
    cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        select.appendChild(option);
    });
    
    // Restore saved location filter from localStorage
    const savedLocation = localStorage.getItem('locationFilter');
    if (savedLocation && cities.includes(savedLocation)) {
        select.value = savedLocation;
        currentLocationFilter = savedLocation;
    }
    
    // Save filter preference on change
    select.addEventListener('change', () => {
        localStorage.setItem('locationFilter', select.value);
    });
}

// Render heat exchangers
async function renderHeatExchangers() {
    const grid = document.getElementById('heat-exchangers-grid');
    
    // Filter heat exchangers by both type and location
    let filteredHeatExchangers = heatExchangers;
    
    // Apply type filter
    if (currentTypeFilter !== 'all') {
        filteredHeatExchangers = filteredHeatExchangers.filter(he => he.type === currentTypeFilter);
    }
    
    // Apply location filter
    if (currentLocationFilter !== 'all') {
        filteredHeatExchangers = filteredHeatExchangers.filter(he => he.location.city === currentLocationFilter);
    }
    
    if (filteredHeatExchangers.length === 0) {
        const filterText = currentTypeFilter === 'all' && currentLocationFilter === 'all' 
            ? 'No heat exchangers found. Add one to get started!' 
            : `No heat exchangers found matching current filters`;
        grid.innerHTML = `<div class="card"><p>${filterText}</p></div>`;
        return;
    }
    
    const cards = await Promise.all(filteredHeatExchangers.map(async he => {
        const data = latestData[he.id];
        return await createHeatExchangerCard(he, data);
    }));
    
    grid.innerHTML = cards.join('');
}

// Create heat exchanger card HTML
async function createHeatExchangerCard(he, data) {
    const statusClass = data ? `status-${data.status}` : '';
    const statusText = data ? data.status.toUpperCase() : 'NO DATA';
    
    // Calculate average pump metrics
    let avgFlow = null;
    let avgSupplyPressure = null;
    let avgReturnPressure = null;
    
    if (he.pump_status) {
        try {
            const pumps = JSON.parse(he.pump_status);
            if (pumps && pumps.length > 0) {
                const validFlows = pumps.filter(p => p.flow_liquid != null).map(p => p.flow_liquid);
                const validSupply = pumps.filter(p => p.pressure_supply != null).map(p => p.pressure_supply);
                const validReturn = pumps.filter(p => p.pressure_return != null).map(p => p.pressure_return);
                
                if (validFlows.length > 0) {
                    avgFlow = (validFlows.reduce((a, b) => a + b, 0) / validFlows.length).toFixed(1);
                }
                if (validSupply.length > 0) {
                    avgSupplyPressure = (validSupply.reduce((a, b) => a + b, 0) / validSupply.length).toFixed(2);
                }
                if (validReturn.length > 0) {
                    avgReturnPressure = (validReturn.reduce((a, b) => a + b, 0) / validReturn.length).toFixed(2);
                }
            }
        } catch (e) {
            console.error('Error parsing pump status:', e);
        }
    }
    
    // Check for active unacknowledged alerts for this heat exchanger
    let hasActiveAlerts = false;
    try {
        const alertResponse = await fetch(`${API_BASE}/alerts/count?heat_exchanger_id=${he.id}&acknowledged=false&resolved=false`);
        if (alertResponse.ok) {
            const alertResult = await alertResponse.json();
            hasActiveAlerts = alertResult.count > 0;
        }
    } catch (error) {
        console.error('Error checking alerts for heat exchanger:', error);
    }
    
    // Check for urgent alarms first (highest priority)
    let hasUrgentAlarms = false;
    let urgentAlarmMessage = '';
    
    if (he.urgent_alarms) {
        try {
            const urgentAlarms = JSON.parse(he.urgent_alarms);
            if (urgentAlarms && urgentAlarms.length > 0) {
                hasUrgentAlarms = true;
                urgentAlarmMessage = `🚨 ${urgentAlarms.length} CRITICAL LOW FLOW ALARM${urgentAlarms.length > 1 ? 'S' : ''}`;
            }
        } catch (e) {
            console.error('Error parsing urgent alarms:', e);
        }
    }
    
    // Check for alarms and fan faults
    let hasAlerts = false;
    let alertMessage = '';
    
    if (!hasUrgentAlarms && he.cdu_alarms) {
        try {
            const alarms = JSON.parse(he.cdu_alarms);
            const hasAlarms = (alarms.fan_alarms && Object.keys(alarms.fan_alarms.Alarms || {}).length > 0) ||
                              (alarms.pump_alarms && Object.keys(alarms.pump_alarms.Alarms || {}).length > 0) ||
                              (alarms.sensor_alarms && alarms.sensor_alarms.Alarms && alarms.sensor_alarms.Alarms.length > 0) ||
                              (alarms.leak_alarms && alarms.leak_alarms.Alarms && alarms.leak_alarms.Alarms.length > 0);
            if (hasAlarms) {
                hasAlerts = true;
                alertMessage = 'Active Alarms';
            }
        } catch (e) {
            console.error('Error parsing alarms:', e);
        }
    }
    
    if (!hasUrgentAlarms && !hasAlerts && he.fan_status) {
        try {
            const fans = JSON.parse(he.fan_status);
            const hasFaults = fans.some(fan => fan.health === 'Fault');
            if (hasFaults) {
                hasAlerts = true;
                alertMessage = 'Fan Faults Detected';
            }
        } catch (e) {
            console.error('Error parsing fan status:', e);
        }
    }
    
    return `
        <div class="card ${hasUrgentAlarms ? 'urgent-alarm-card' : ''}">
            <h3>${he.name}</h3>
            ${he.type ? `<div style="display: inline-block; padding: 0.25rem 0.5rem; background-color: var(--secondary-color); color: white; border-radius: 4px; font-size: 0.85rem; margin-top: 0.5rem;">${he.type}</div>` : ''}
            <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #888;">
                <p>📍 ${he.location.city}, ${he.location.building}</p>
                <p>🚪 Room ${he.location.room}, Tile ${he.location.tile}</p>
                <p>🌐 ${he.rscm_ip}</p>
            </div>
            
            ${hasUrgentAlarms ? `
                <div style="margin-top: 1rem; padding: 1rem; background-color: rgba(244, 67, 54, 0.2); border: 2px solid var(--danger-color); border-radius: 4px;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--danger-color); font-weight: bold; font-size: 1.1em;">
                        <span class="alarm-icon" style="font-size: 1.5em;">🚨</span>
                        ${urgentAlarmMessage}
                    </div>
                </div>
            ` : ''}
            
            ${data ? `
                <div style="margin-top: 1rem; padding: 1rem; background-color: rgba(100, 108, 255, 0.1); border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span>Status:</span>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span>Ambient Temperature:</span>
                        <strong>${data.temperature.toFixed(1)}°C</strong>
                    </div>
                    ${avgFlow !== null ? `
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Avg Flow:</span>
                            <strong>${avgFlow} L/min</strong>
                        </div>
                    ` : ''}
                    ${avgSupplyPressure !== null ? `
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Avg Supply Pressure:</span>
                            <strong>${avgSupplyPressure} kPa</strong>
                        </div>
                    ` : ''}
                    ${avgReturnPressure !== null ? `
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Avg Return Pressure:</span>
                            <strong>${avgReturnPressure} kPa</strong>
                        </div>
                    ` : ''}
                    ${hasAlerts && !hasUrgentAlarms ? `
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span>Alerts:</span>
                            <strong style="color: var(--warning-color); display: flex; align-items: center; gap: 0.3rem;">
                                <span class="alarm-icon" style="font-size: 1em;">⚠️</span>
                                ${alertMessage}
                            </strong>
                        </div>
                    ` : ''}
                </div>
            ` : `
                <div style="margin-top: 1rem; padding: 1rem; background-color: rgba(100, 108, 255, 0.1); border-radius: 4px; text-align: center;">
                    <div style="color: #888; font-size: 0.95rem;">
                        <div style="margin-bottom: 0.5rem;">⏳</div>
                        <div>Waiting on initial polling...</div>
                        <div style="font-size: 0.85rem; margin-top: 0.25rem;">Data will be available shortly</div>
                    </div>
                </div>
            `}
            
            ${hasActiveAlerts ? '<span class="alert-indicator"></span>' : ''}
            
            <div style="margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <button onclick="window.location.href='${pathPrefix}/heat-exchanger/${he.id}'" class="btn">View Details</button>
                ${isAdmin ? `<button onclick="window.location.href='${pathPrefix}/heat-exchanger-form?id=${he.id}'" class="btn btn-secondary">Edit</button>` : ''}
                ${isAdmin ? `<button onclick="deleteHeatExchanger(${he.id}, '${he.name}')" class="btn btn-danger">Delete</button>` : ''}
            </div>
        </div>
    `;
}

// WebSocket connection
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}${pathPrefix}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        updateWSStatus(true);
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWSMessage(message);
        
        // Update alert badge when new alert arrives
        if (message.type === 'new_alert') {
            updateAlertBadge();
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateWSStatus(false);
        
        // Reconnect after 5 seconds
        if (!reconnectInterval) {
            reconnectInterval = setInterval(connectWebSocket, 5000);
        }
    };
}

// Handle WebSocket messages
function handleWSMessage(message) {
    if (message.type === 'monitoring_update' && message.heat_exchanger_id) {
        latestData[message.heat_exchanger_id] = {
            ...message.data,
            heat_exchanger_id: message.heat_exchanger_id
        };
        renderHeatExchangers();
    }
}

// Update WebSocket status
function updateWSStatus(connected) {
    const statusEl = document.getElementById('ws-status');
    if (connected) {
        statusEl.textContent = '🟢 Live';
        statusEl.className = 'ws-status connected';
    } else {
        statusEl.textContent = '🔴 Disconnected';
        statusEl.className = 'ws-status disconnected';
    }
}

// Update alert badge with active alert count
async function updateAlertBadge() {
    try {
        const response = await fetch(`${API_BASE}/alerts/count?acknowledged=false&resolved=false`);
        if (!response.ok) return;
        
        const result = await response.json();
        const count = result.count || 0;
        
        const badge = document.getElementById('alertBadge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    } catch (error) {
        console.error('Error fetching alert count:', error);
    }
}

// Delete heat exchanger
async function deleteHeatExchanger(id, name) {
    if (!confirm(`Are you sure you want to delete "${name}"?\n\nThis will permanently delete:\n- The heat exchanger\n- All monitoring data\n- All associated alerts\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/heat-exchangers/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            // Remove from local array
            heatExchangers = heatExchangers.filter(he => he.id !== id);
            delete latestData[id];
            
            // Re-render
            renderHeatExchangers(currentFilter);
            
            // Show success message briefly
            const grid = document.getElementById('heat-exchangers-grid');
            const successMsg = document.createElement('div');
            successMsg.style.cssText = 'position: fixed; top: 20px; right: 20px; background: var(--success-color); color: white; padding: 1rem; border-radius: 4px; z-index: 1000;';
            successMsg.textContent = `Successfully deleted "${name}"`;
            document.body.appendChild(successMsg);
            setTimeout(() => successMsg.remove(), 3000);
        } else {
            const error = await response.json();
            alert(`Failed to delete heat exchanger: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error deleting heat exchanger:', error);
        alert('Error deleting heat exchanger. Please try again.');
    }
}
