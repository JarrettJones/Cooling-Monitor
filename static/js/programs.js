// Programs management
window.programsList = window.programsList || [];

// Load programs when section is active
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on settings page
    if (window.location.pathname.includes('settings')) {
        loadPrograms();
        setupProgramHandlers();
    }
});

async function loadPrograms() {
    try {
        const response = await fetch(`${API_BASE}/programs/`);
        window.programsList = await response.json();
        renderPrograms();
    } catch (error) {
        console.error('Error loading programs:', error);
        document.getElementById('programList').innerHTML = '<p style="color: var(--danger-color);">Failed to load programs</p>';
    }
}

function renderPrograms() {
    const list = document.getElementById('programList');
    
    if (window.programsList.length === 0) {
        list.innerHTML = '<p style="color: var(--text-secondary);">No programs defined. Add one above.</p>';
        return;
    }
    
    list.innerHTML = window.programsList.map(program => `
        <div class="program-item">
            <span>${program.name}</span>
            <button onclick="deleteProgram(${program.id}, '${program.name}')" class="btn btn-danger" style="padding: 0.4rem 0.8rem; font-size: 0.875rem;">
                Delete
            </button>
        </div>
    `).join('');
}

function setupProgramHandlers() {
    const form = document.getElementById('addProgramForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const nameInput = document.getElementById('new_program_name');
        const programName = nameInput.value.trim();
        
        if (!programName) return;
        
        try {
            const response = await fetch(`${API_BASE}/programs/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: programName })
            });
            
            if (response.ok) {
                nameInput.value = '';
                await loadPrograms();
                showSuccessMessage('Program added successfully');
            } else {
                const error = await response.json();
                alert('Error: ' + (error.detail || 'Failed to add program'));
            }
        } catch (error) {
            console.error('Error adding program:', error);
            alert('Failed to add program');
        }
    });
}

async function deleteProgram(id, name) {
    if (!confirm(`Delete program "${name}"?\\n\\nWarning: Heat exchangers assigned to this program will lose their program assignment.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/programs/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadPrograms();
            showSuccessMessage('Program deleted successfully');
        } else {
            const error = await response.json();
            alert('Error: ' + (error.detail || 'Failed to delete program'));
        }
    } catch (error) {
        console.error('Error deleting program:', error);
        alert('Failed to delete program');
    }
}

function showSuccessMessage(message) {
    // Create a temporary success message
    const msg = document.createElement('div');
    msg.textContent = '✓ ' + message;
    msg.style.cssText = 'position: fixed; top: 20px; right: 20px; background-color: var(--success-color); color: white; padding: 1rem 1.5rem; border-radius: 6px; z-index: 1000; animation: slideIn 0.3s ease-out;';
    document.body.appendChild(msg);
    
    setTimeout(() => {
        msg.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => msg.remove(), 300);
    }, 3000);
}
