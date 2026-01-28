// Check if editing
const isEdit = HEAT_EXCHANGER_ID && HEAT_EXCHANGER_ID.length > 0;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadPrograms();
    
    if (isEdit) {
        document.getElementById('form-title').textContent = 'Edit Heat Exchanger';
        document.getElementById('submit-btn').textContent = 'Update';
        await fetchHeatExchanger();
    }
    
    setupForm();
});

// Load programs into dropdown
async function loadPrograms() {
    try {
        console.log('Loading programs...');
        const response = await fetch(`${API_BASE}/programs/`);
        if (!response.ok) {
            throw new Error(`Failed to fetch programs: ${response.status}`);
        }
        const programs = await response.json();
        console.log('Programs loaded:', programs);
        
        const select = document.getElementById('program');
        if (!select) {
            console.error('Program select element not found!');
            return;
        }
        
        // Clear existing options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        programs.forEach(program => {
            const option = document.createElement('option');
            option.value = program.id;
            option.textContent = program.name;
            select.appendChild(option);
        });
        console.log('Programs added to dropdown');
    } catch (error) {
        console.error('Failed to load programs:', error);
    }
}

// Fetch heat exchanger for editing
async function fetchHeatExchanger() {
    try {
        const response = await fetch(`${API_BASE}/heat-exchangers/${HEAT_EXCHANGER_ID}`);
        const he = await response.json();
        
        document.getElementById('name').value = he.name;
        document.getElementById('type').value = he.type || '';
        document.getElementById('program').value = he.program_id || '';
        document.getElementById('rscm_ip').value = he.rscm_ip;
        document.getElementById('city').value = he.location.city;
        document.getElementById('building').value = he.location.building;
        document.getElementById('room').value = he.location.room;
        document.getElementById('tile').value = he.location.tile;
    } catch (error) {
        showError('Failed to load heat exchanger');
    }
}

// Setup form submission
function setupForm() {
    document.getElementById('heat-exchanger-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('name').value,
            type: document.getElementById('type').value,
            rscm_ip: document.getElementById('rscm_ip').value,
            location: {
                city: document.getElementById('city').value,
                building: document.getElementById('building').value,
                room: document.getElementById('room').value,
                tile: document.getElementById('tile').value
            },
            program_id: parseInt(document.getElementById('program').value) || null,
            is_active: true
        };
        
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';
        
        try {
            const url = isEdit ? 
                `${API_BASE}/heat-exchangers/${HEAT_EXCHANGER_ID}` : 
                `${API_BASE}/heat-exchangers/`;
            
            const method = isEdit ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                // Show success message briefly before redirecting
                submitBtn.textContent = '✓ Saved!';
                submitBtn.style.backgroundColor = 'var(--success-color)';
                
                setTimeout(() => {
                    navigateTo('/');
                }, 1500);
            } else {
                const error = await response.json();
                showError(error.detail || 'Failed to save heat exchanger');
                submitBtn.disabled = false;
                submitBtn.textContent = isEdit ? 'Update' : 'Create';
            }
        } catch (error) {
            showError('Error saving heat exchanger');
            submitBtn.disabled = false;
            submitBtn.textContent = isEdit ? 'Update' : 'Create';
        }
    });
}

// Show error message
function showError(message) {
    const errorEl = document.getElementById('error-message');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
    
    setTimeout(() => {
        errorEl.style.display = 'none';
    }, 5000);
}
