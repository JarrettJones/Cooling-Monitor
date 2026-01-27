// User Management JavaScript

let users = [];
let editingUserId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    setupEventListeners();
});

// Check user role and display current user
async function checkUserRole() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`);
        if (response.ok) {
            const user = await response.json();
            document.getElementById('currentUser').textContent = `👤 ${user.username}`;
        } else {
            navigateTo('/login');
        }
    } catch (error) {
        console.error('Error checking user role:', error);
        navigateTo('/login');
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('addUserBtn').addEventListener('click', () => {
        openModal();
    });

    document.getElementById('cancelBtn').addEventListener('click', () => {
        closeModal();
    });

    document.getElementById('userForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveUser();
    });

    document.getElementById('logoutBtn').addEventListener('click', logout);
}

// Load all users
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/users/`);
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                navigateTo('/login');
                return;
            }
            throw new Error('Failed to load users');
        }

        users = await response.json();
        renderUsers();
    } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('usersBody').innerHTML = 
            '<tr><td colspan="4" style="text-align: center; color: var(--danger-color);">Failed to load users</td></tr>';
    }
}

// Render users table
function renderUsers() {
    const tbody = document.getElementById('usersBody');

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No users found</td></tr>';
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr>
            <td>
                ${escapeHtml(user.username)}
                ${!user.is_active ? '<span style="color: var(--warning-color); font-size: 0.875rem; margin-left: 0.5rem;">(Pending)</span>' : ''}
            </td>
            <td><span class="role-badge role-${user.role}">${user.role}</span></td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                ${!user.is_active ? `
                    <button class="btn btn-success btn-small" onclick="approveUser(${user.id}, '${escapeHtml(user.username)}')">Approve</button>
                    <button class="btn btn-danger btn-small" onclick="denyUser(${user.id}, '${escapeHtml(user.username)}')">Deny</button>
                ` : `
                    <button class="btn btn-secondary btn-small" onclick="editUser(${user.id})">Edit</button>
                    <button class="btn btn-danger btn-small" onclick="deleteUser(${user.id}, '${escapeHtml(user.username)}')">Delete</button>
                `}
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-small" onclick="editUser(${user.id})">Edit</button>
                    <button class="btn btn-small btn-danger" onclick="deleteUser(${user.id}, '${escapeHtml(user.username)}')">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Open modal for creating/editing user
function openModal(user = null) {
    const modal = document.getElementById('userModal');
    const form = document.getElementById('userForm');
    const title = document.getElementById('modalTitle');
    const passwordInput = document.getElementById('password');
    const passwordHelp = document.getElementById('passwordHelp');

    form.reset();

    if (user) {
        // Edit mode
        editingUserId = user.id;
        title.textContent = 'Edit User';
        document.getElementById('userId').value = user.id;
        document.getElementById('username').value = user.username;
        document.getElementById('username').disabled = true; // Don't allow changing username
        document.getElementById('role').value = user.role;
        passwordInput.required = false;
        passwordHelp.textContent = 'Leave blank to keep current password';
    } else {
        // Create mode
        editingUserId = null;
        title.textContent = 'Add New User';
        document.getElementById('username').disabled = false;
        passwordInput.required = true;
        passwordHelp.textContent = 'Minimum 6 characters';
    }

    modal.style.display = 'flex';
}

// Close modal
function closeModal() {
    document.getElementById('userModal').style.display = 'none';
    document.getElementById('userForm').reset();
    editingUserId = null;
}

// Save user (create or update)
async function saveUser() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    const userData = {
        username,
        role
    };

    // Only include password if provided
    if (password) {
        userData.password = password;
    }

    try {
        let response;

        if (editingUserId) {
            // Update existing user
            response = await fetch(`${API_BASE}/users/${editingUserId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
        } else {
            // Create new user
            if (!password) {
                alert('Password is required for new users');
                return;
            }
            response = await fetch(`${API_BASE}/users/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save user');
        }

        closeModal();
        await loadUsers();
    } catch (error) {
        console.error('Error saving user:', error);
        alert(`Error: ${error.message}`);
    }
}

// Edit user
function editUser(userId) {
    const user = users.find(u => u.id === userId);
    if (user) {
        openModal(user);
    }
}

// Delete user
async function deleteUser(userId, username) {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/users/${userId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete user');
        }

        await loadUsers();
    } catch (error) {
        console.error('Error deleting user:', error);
        alert(`Error: ${error.message}`);
    }
}

// Approve user
async function approveUser(userId, username) {
    if (!confirm(`Approve registration for "${username}"?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/users/${userId}/approve`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to approve user');
        }

        const result = await response.json();
        alert(result.message);
        await loadUsers();
    } catch (error) {
        console.error('Error approving user:', error);
        alert(`Error: ${error.message}`);
    }
}

// Deny user registration
async function denyUser(userId, username) {
    if (!confirm(`Deny and delete registration for "${username}"?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/users/${userId}/deny`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to deny user');
        }

        const result = await response.json();
        alert(result.message);
        await loadUsers();
    } catch (error) {
        console.error('Error denying user:', error);
        alert(`Error: ${error.message}`);
    }
}

// Logout
async function logout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
        navigateTo('/login');
    } catch (error) {
        console.error('Logout error:', error);
        navigateTo('/login');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
