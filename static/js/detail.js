// API Base URL
const API_BASE = '/api';

// Charts
let temperatureChart;

// Data
let monitoringData = [];
let currentHeatExchanger = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (HEAT_EXCHANGER_ID) {
        checkUserRole(); // From auth.js
        checkAdminButtons(); // Local function for Edit/Delete buttons
        fetchData();
        setupEventListeners();
        connectWebSocket();
    }
});

// Check if user can edit/delete (admin only)
async function checkAdminButtons() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            const user = await response.json();
            if (user.is_admin) {
                // Show admin buttons
                document.getElementById('edit-btn').style.display = 'inline-block';
                document.getElementById('delete-btn').style.display = 'inline-block';
            }
        }
    } catch (error) {
        console.log('Not authenticated or error checking role:', error);
    }
}

// Fetch data
async function fetchData() {
    try {
        const [heResponse, dataResponse] = await Promise.all([
            fetch(`${API_BASE}/heat-exchangers/${HEAT_EXCHANGER_ID}`),
            fetch(`${API_BASE}/monitoring/${HEAT_EXCHANGER_ID}?limit=100`)
        ]);
        
        const heatExchanger = await heResponse.json();
        monitoringData = await dataResponse.json();
        
        currentHeatExchanger = heatExchanger;
        
        renderHeatExchanger(heatExchanger);
        renderFanStatus(heatExchanger);
        renderPumpStatus(heatExchanger);
        renderCurrentReadings();
        renderCharts();
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('heat-exchanger-name').textContent = 'Error loading data';
    }
}

// Render heat exchanger info
function renderHeatExchanger(he) {
    document.getElementById('heat-exchanger-name').textContent = he.name;
    
    const latest = monitoringData[0];
    const statusBadge = latest ? 
        `<span class="status-badge status-${latest.status}">${latest.status.toUpperCase()}</span>` : 
        'N/A';
    
    document.getElementById('info-content').innerHTML = `
        <div>
            <strong>Location:</strong>
            <p>${he.location.city}, ${he.location.building}</p>
            <p>Room ${he.location.room}, Tile ${he.location.tile}</p>
        </div>
        <div>
            <strong>R-SCM IP:</strong>
            <p>${he.rscm_ip}</p>
        </div>
        <div>
            <strong>Status:</strong>
            <p>${he.is_active ? '✅ Active' : '❌ Inactive'}</p>
        </div>
        <div>
            <strong>Current Status:</strong>
            <p>${statusBadge}</p>
        </div>
        ${he.manager_type ? `
            <div>
                <strong>Manager Type:</strong>
                <p>${he.manager_type}</p>
            </div>
        ` : ''}
        ${he.model ? `
            <div>
                <strong>Model:</strong>
                <p>${he.model}</p>
            </div>
        ` : ''}
        ${he.firmware_version ? `
            <div>
                <strong>Firmware Version:</strong>
                <p>${he.firmware_version}</p>
            </div>
        ` : ''}
        ${he.status_state ? `
            <div>
                <strong>State:</strong>
                <p>${he.status_state}</p>
            </div>
        ` : ''}
        ${he.status_health ? `
            <div>
                <strong>Health:</strong>
                <p>${he.status_health}</p>
            </div>
        ` : ''}
        ${he.hostname ? `
            <div>
                <strong>Hostname:</strong>
                <p>${he.hostname}</p>
            </div>
        ` : ''}
        ${he.unique_id ? `
            <div>
                <strong>Unique ID:</strong>
                <p>${he.unique_id}</p>
            </div>
        ` : ''}
        ${he.time_since_boot ? `
            <div>
                <strong>Time Since Boot:</strong>
                <p>${he.time_since_boot}</p>
            </div>
        ` : ''}
    `;
    
    // Render CDU Controller Status if available
    if (he.cdu_controller_status) {
        renderCDUStatus(he);
    } else {
        document.getElementById('cdu-controller-status').style.display = 'none';
    }
}

// Render CDU Controller Status
function renderCDUStatus(he) {
    try {
        const controllerStatus = JSON.parse(he.cdu_controller_status || '{}');
        const chassisStatus = JSON.parse(he.cdu_chassis_status || '{}');
        const alarms = JSON.parse(he.cdu_alarms || '{}');
        
        document.getElementById('cdu-controller-status').style.display = 'block';
        
        document.getElementById('cdu-content').innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
                <div>
                    <strong>Chassis State:</strong>
                    <p>${chassisStatus.state || 'N/A'}</p>
                </div>
                <div>
                    <strong>Chassis Health:</strong>
                    <p>${chassisStatus.health || 'N/A'}</p>
                </div>
                <div>
                    <strong>Unit On:</strong>
                    <p>${controllerStatus.UnitOn ? '✅' : '❌'}</p>
                </div>
                <div>
                    <strong>General Alarm State:</strong>
                    <p>${controllerStatus.GeneralAlarmState ? '⚠️ Yes' : '✅ No'}</p>
                </div>
                <div>
                    <strong>Max Cooling Active:</strong>
                    <p>${controllerStatus.MaxCoolingActive ? '✅ Yes' : '❌ No'}</p>
                </div>
                <div>
                    <strong>Ambient Temperature:</strong>
                    <p>${controllerStatus.AmbientTemperature ? controllerStatus.AmbientTemperature + '°C' : 'N/A'}</p>
                </div>
                <div>
                    <strong>Ambient Humidity:</strong>
                    <p>${controllerStatus.AmbientHumidity ? controllerStatus.AmbientHumidity + '%' : 'N/A'}</p>
                </div>
                <div>
                    <strong>Pump 1:</strong>
                    <p>${controllerStatus.Pump1Active ? '✅' : '❌'}</p>
                </div>
                <div>
                    <strong>Pump 2:</strong>
                    <p>${controllerStatus.Pump2Active ? '✅' : '❌'}</p>
                </div>
                <div>
                    <strong>Pump 3:</strong>
                    <p>${controllerStatus.Pump3Active ? '✅' : '❌'}</p>
                </div>
                <div>
                    <strong>Pump 4:</strong>
                    <p>${controllerStatus.Pump4Active ? '✅' : '❌'}</p>
                </div>
                <div>
                    <strong>Pump 5:</strong>
                    <p>${controllerStatus.Pump5Active ? '✅' : '❌'}</p>
                </div>
            </div>
            
            ${renderCDUAlarms(alarms)}
            ${renderBoardErrors(controllerStatus)}
        `;
    } catch (e) {
        console.error('Error rendering CDU status:', e);
    }
}

// Render Fan Status in separate tile
function renderFanStatus(he) {
    try {
        const fanStatus = JSON.parse(he.fan_status || '[]');
        
        if (!fanStatus || fanStatus.length === 0) {
            document.getElementById('fan-status-card').style.display = 'none';
            return;
        }
        
        document.getElementById('fan-status-card').style.display = 'block';
        
        // Check if any fan has Fault status
        const hasFaults = fanStatus.some(fan => fan.health === 'Fault');
        
        const fanTableHtml = `
            <table class="alarm-table">
                <thead>
                    <tr>
                        <th>Fan ID</th>
                        <th>State</th>
                        <th>Health</th>
                        <th>Speed %</th>
                    </tr>
                </thead>
                <tbody>
                    ${fanStatus.map(fan => `
                        <tr>
                            <td>${fan.name || fan.id}</td>
                            <td>${fan.state || 'N/A'}</td>
                            <td>${fan.health || 'N/A'}</td>
                            <td>${fan.speed_percent !== null && fan.speed_percent !== undefined ? fan.speed_percent + '%' : 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        document.getElementById('fan-status-content').innerHTML = `
            <div class="fan-section">
                <div class="fan-header" onclick="toggleFans()" style="cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                    <h4 style="margin: 0;">Fans (${fanStatus.length})</h4>
                    ${hasFaults ? '<span class="alarm-icon">⚠️</span>' : ''}
                    <span id="fan-toggle" style="margin-left: auto;">▼</span>
                </div>
                <div id="fan-content" style="display: none; margin-top: 0.5rem;">
                    ${fanTableHtml}
                </div>
            </div>
        `;
    } catch (e) {
        console.error('Error rendering fan status:', e);
    }
}

// Toggle fan visibility
function toggleFans() {
    const content = document.getElementById('fan-content');
    const toggle = document.getElementById('fan-toggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.textContent = '▲';
    } else {
        content.style.display = 'none';
        toggle.textContent = '▼';
    }
}

// Render Pump Status in separate tile
function renderPumpStatus(he) {
    try {
        const pumpStatus = JSON.parse(he.pump_status || '[]');
        
        if (!pumpStatus || pumpStatus.length === 0) {
            document.getElementById('pump-status-card').style.display = 'none';
            return;
        }
        
        document.getElementById('pump-status-card').style.display = 'block';
        
        // Check if any pump has error
        const hasErrors = pumpStatus.some(pump => pump.error_code !== null);
        
        const pumpTableHtml = `
            <table class="alarm-table">
                <thead>
                    <tr>
                        <th>Pump ID</th>
                        <th>Status</th>
                        <th>Speed %</th>
                        <th>Requested %</th>
                        <th>Flow (L/min)</th>
                        <th>Supply (kPa)</th>
                        <th>Return (kPa)</th>
                        <th>Diff (kPa)</th>
                        <th>pH</th>
                    </tr>
                </thead>
                <tbody>
                    ${pumpStatus.map(pump => `
                        <tr>
                            <td>${pump.name || pump.id}</td>
                            <td>${pump.status || 'N/A'}</td>
                            <td>${pump.speed !== null && pump.speed !== undefined ? pump.speed + '%' : 'N/A'}</td>
                            <td>${pump.requested_speed !== null && pump.requested_speed !== undefined ? pump.requested_speed + '%' : 'N/A'}</td>
                            <td>${pump.flow_liquid !== null && pump.flow_liquid !== undefined && typeof pump.flow_liquid === 'number' ? pump.flow_liquid.toFixed(1) : 'N/A'}</td>
                            <td>${pump.pressure_supply !== null && pump.pressure_supply !== undefined ? pump.pressure_supply : 'N/A'}</td>
                            <td>${pump.pressure_return !== null && pump.pressure_return !== undefined ? pump.pressure_return : 'N/A'}</td>
                            <td>${pump.pressure_diff !== null && pump.pressure_diff !== undefined ? pump.pressure_diff : 'N/A'}</td>
                            <td>${pump.liquid_ph !== null && pump.liquid_ph !== undefined && typeof pump.liquid_ph === 'number' ? pump.liquid_ph.toFixed(2) : 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        // Generate charts HTML for each pump
        const pumpChartsHtml = pumpStatus.map((pump, index) => {
            const pumpName = pump.name || pump.id || `Pump ${index + 1}`;
            return `
                <div class="pump-chart-section" style="margin-top: 1rem; border-top: 1px solid #ddd; padding-top: 1rem;">
                    <div class="pump-chart-header" onclick="togglePumpChart(${index})" style="cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                        <h5 style="margin: 0;">${pumpName} - Performance History</h5>
                        <span id="pump-chart-toggle-${index}" style="margin-left: auto;">▶</span>
                    </div>
                    <div id="pump-chart-${index}" style="display: none; margin-top: 0.5rem;">
                        <canvas id="pumpCanvas${index}" style="max-height: 300px;"></canvas>
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('pump-status-content').innerHTML = `
            <div class="pump-section">
                <div class="pump-header" onclick="togglePumps()" style="cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                    <h4 style="margin: 0;">Pumps (${pumpStatus.length})</h4>
                    ${hasErrors ? '<span class="alarm-icon">⚠️</span>' : ''}
                    <span id="pump-toggle" style="margin-left: auto;">▼</span>
                </div>
                <div id="pump-content" style="display: none; margin-top: 0.5rem;">
                    ${pumpTableHtml}
                    ${pumpChartsHtml}
                </div>
            </div>
        `;
        
        // Render charts for each pump
        pumpStatus.forEach((pump, index) => {
            renderSinglePumpChart(index);
        });
        
    } catch (e) {
        console.error('Error rendering pump status:', e);
    }
}

// Toggle pump chart visibility
function togglePumpChart(index) {
    const content = document.getElementById(`pump-chart-${index}`);
    const toggle = document.getElementById(`pump-chart-toggle-${index}`);
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.textContent = '▼';
    } else {
        content.style.display = 'none';
        toggle.textContent = '▶';
    }
}

// Toggle pump visibility
function togglePumps() {
    const content = document.getElementById('pump-content');
    const toggle = document.getElementById('pump-toggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.textContent = '▲';
    } else {
        content.style.display = 'none';
        toggle.textContent = '▼';
    }
}

// Render CDU Alarms
function renderCDUAlarms(alarms) {
    const hasAlarms = (alarms.fan_alarms && Object.keys(alarms.fan_alarms.Alarms || {}).length > 0) ||
                      (alarms.pump_alarms && Object.keys(alarms.pump_alarms.Alarms || {}).length > 0) ||
                      (alarms.sensor_alarms && alarms.sensor_alarms.Alarms && alarms.sensor_alarms.Alarms.length > 0) ||
                      (alarms.leak_alarms && alarms.leak_alarms.Alarms && alarms.leak_alarms.Alarms.length > 0);
    
    if (!hasAlarms) return '';
    
    // Build alarm content
    let alarmsContent = '';
    
    if (alarms.fan_alarms && Object.keys(alarms.fan_alarms.Alarms || {}).length > 0) {
        alarmsContent += `
            <div style="margin-bottom: 1rem;">
                <strong>Fan Alarms (${alarms.fan_alarms.Status?.Health}):</strong>
                <table class="alarm-table">
                    <thead>
                        <tr>
                            <th>Fan ID</th>
                            <th>Alarm Details</th>
                        </tr>
                    </thead>
                    <tbody>`;
        for (const [fan, alarmList] of Object.entries(alarms.fan_alarms.Alarms)) {
            alarmsContent += `
                        <tr>
                            <td>Fan ${fan}</td>
                            <td>${alarmList.join(', ')}</td>
                        </tr>`;
        }
        alarmsContent += `
                    </tbody>
                </table>
            </div>`;
    }
    
    if (alarms.sensor_alarms && alarms.sensor_alarms.Alarms && alarms.sensor_alarms.Alarms.length > 0) {
        alarmsContent += `
            <div style="margin-bottom: 1rem;">
                <strong>Sensor Alarms (${alarms.sensor_alarms.Status?.Health}):</strong>
                <table class="alarm-table">
                    <thead>
                        <tr>
                            <th>Alarm Type</th>
                        </tr>
                    </thead>
                    <tbody>`;
        alarms.sensor_alarms.Alarms.forEach(alarm => {
            alarmsContent += `
                        <tr>
                            <td>${alarm}</td>
                        </tr>`;
        });
        alarmsContent += `
                    </tbody>
                </table>
            </div>`;
    }
    
    if (alarms.leak_alarms && alarms.leak_alarms.Alarms && alarms.leak_alarms.Alarms.length > 0) {
        alarmsContent += `
            <div style="margin-bottom: 1rem;">
                <strong>Leak Alarms (${alarms.leak_alarms.Status?.Health}):</strong>
                <table class="alarm-table">
                    <thead>
                        <tr>
                            <th>Alarm Type</th>
                        </tr>
                    </thead>
                    <tbody>`;
        alarms.leak_alarms.Alarms.forEach(alarm => {
            alarmsContent += `
                        <tr>
                            <td>${alarm}</td>
                        </tr>`;
        });
        alarmsContent += `
                    </tbody>
                </table>
            </div>`;
    }
    
    return `
        <div class="alarm-section" style="margin-top: 1rem;">
            <div class="alarm-header" onclick="toggleAlarms()" style="cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                <h4 style="margin: 0;">Alarms</h4>
                <span class="alarm-icon">🔴</span>
                <span id="alarm-toggle" style="margin-left: auto;">▼</span>
            </div>
            <div id="alarm-content" class="alarm-content" style="display: none; margin-top: 0.5rem;">
                ${alarmsContent}
            </div>
        </div>
    `;
}

// Toggle alarms visibility
function toggleAlarms() {
    const content = document.getElementById('alarm-content');
    const toggle = document.getElementById('alarm-toggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.textContent = '▲';
    } else {
        content.style.display = 'none';
        toggle.textContent = '▼';
    }
}

// Render Board Errors
function renderBoardErrors(controllerStatus) {
    const errors = [];
    if (controllerStatus.HruBoardError) errors.push('HRU Board');
    if (controllerStatus.ControlIOError) errors.push('Control IO');
    if (controllerStatus.RPUDriverBoardError) errors.push('RPU Driver Board');
    for (let i = 1; i <= 9; i++) {
        if (controllerStatus[`FanControlBoard${i}Error`]) {
            errors.push(`Fan Control Board ${i}`);
        }
    }
    
    if (errors.length === 0) return '';
    
    return `
        <div style="margin-top: 1rem;">
            <h4 style="color: var(--danger-color);">Board Errors</h4>
            <ul>
                ${errors.map(e => `<li>${e}</li>`).join('')}
            </ul>
        </div>
    `;
}

// Render current readings
function renderCurrentReadings() {
    const latest = monitoringData[0];
    const container = document.getElementById('current-readings');
    
    if (!latest) {
        container.innerHTML = '<p>No data available</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="metric">
            <strong>Ambient Temperature</strong>
            <div class="metric-value" style="color: var(--primary-color);">
                ${latest.temperature.toFixed(1)}°C
            </div>
        </div>
    `;
}

// Render charts
function renderCharts() {
    const reversedData = [...monitoringData].reverse();
    const labels = reversedData.map(d => new Date(d.timestamp).toLocaleTimeString());
    
    // Temperature chart - only ambient temperature and humidity
    const tempCtx = document.getElementById('temperatureChart').getContext('2d');
    if (temperatureChart) temperatureChart.destroy();
    
    const datasets = [];
    
    // Add ambient temperature if available
    if (reversedData.some(d => d.ambient_temperature != null)) {
        datasets.push({
            label: 'Ambient Temperature (°C)',
            data: reversedData.map(d => d.ambient_temperature),
            borderColor: '#ff6b6b',
            backgroundColor: 'rgba(255, 107, 107, 0.1)',
            tension: 0.4,
            yAxisID: 'y'
        });
    }
    
    // Add ambient humidity if available
    if (reversedData.some(d => d.ambient_humidity != null)) {
        datasets.push({
            label: 'Ambient Humidity (%)',
            data: reversedData.map(d => d.ambient_humidity),
            borderColor: '#51cf66',
            backgroundColor: 'rgba(81, 207, 102, 0.1)',
            tension: 0.4,
            yAxisID: 'y1'
        });
    }
    
    temperatureChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { 
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: reversedData.some(d => d.ambient_humidity != null),
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Humidity (%)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Render individual pump chart
function renderSinglePumpChart(pumpIndex) {
    const ctx = document.getElementById(`pumpCanvas${pumpIndex}`);
    if (!ctx || monitoringData.length === 0) {
        console.log(`No canvas or data for pump ${pumpIndex}`);
        return;
    }
    
    console.log(`Rendering pump ${pumpIndex}, total monitoring records: ${monitoringData.length}`);
    
    // Reverse data for chronological order (oldest to newest)
    const chartData = [...monitoringData].reverse();
    
    // Extract pump data from raw_data in monitoring history
    const pumpHistoryData = chartData.map((d, idx) => {
        try {
            if (d.raw_data) {
                const rawData = typeof d.raw_data === 'string' ? JSON.parse(d.raw_data) : d.raw_data;
                
                // Debug first record
                if (idx === 0) {
                    console.log('First record raw_data keys:', Object.keys(rawData));
                    console.log('pump_status exists:', 'pump_status' in rawData);
                    console.log('pump_status value:', rawData.pump_status);
                }
                
                const pumps = rawData.pump_status || [];
                return pumps[pumpIndex] || null;
            }
            return null;
        } catch (e) {
            console.error('Error parsing pump data at index', idx, ':', e);
            return null;
        }
    });
    
    const validPoints = pumpHistoryData.filter(p => p !== null).length;
    console.log(`Pump ${pumpIndex} history data:`, validPoints, 'valid points out of', pumpHistoryData.length);
    
    // If no historical data available, show message
    if (validPoints === 0) {
        ctx.parentElement.innerHTML = '<p style="padding: 1rem; text-align: center; color: #666;">⏳ Historical pump data will appear after the next monitoring cycle (polling interval: check Settings)</p>';
        return;
    }
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.map(d => new Date(d.timestamp).toLocaleTimeString()),
            datasets: [
                {
                    label: 'Flow (L/min)',
                    data: pumpHistoryData.map(p => p?.flow_liquid ?? null),
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'Supply Pressure (kPa)',
                    data: pumpHistoryData.map(p => p?.pressure_supply ?? null),
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4
                },
                {
                    label: 'Return Pressure (kPa)',
                    data: pumpHistoryData.map(p => p?.pressure_return ?? null),
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Flow (L/min)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Pressure (kPa)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('edit-btn').addEventListener('click', () => {
        window.location.href = `/heat-exchanger-form?id=${HEAT_EXCHANGER_ID}`;
    });
    
    document.getElementById('delete-btn').addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete this heat exchanger?')) {
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/heat-exchangers/${HEAT_EXCHANGER_ID}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                window.location.href = '/';
            } else {
                alert('Failed to delete heat exchanger');
            }
        } catch (error) {
            alert('Error deleting heat exchanger');
        }
    });
}

// WebSocket for real-time updates
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'monitoring_update' && message.heat_exchanger_id === HEAT_EXCHANGER_ID) {
            // Add new data point
            monitoringData.unshift({
                ...message.data,
                timestamp: message.data.timestamp
            });
            
            // Keep only last 100 points
            if (monitoringData.length > 100) {
                monitoringData = monitoringData.slice(0, 100);
            }
            
            renderCurrentReadings();
            renderCharts();
            
            // Fetch updated heat exchanger data to get latest pump status
            fetch(`${API_BASE}/heat-exchangers/${HEAT_EXCHANGER_ID}`)
                .then(r => r.json())
                .then(he => {
                    currentHeatExchanger = he;
                    renderPumpStatus(he);
                });
        }
    };
}
