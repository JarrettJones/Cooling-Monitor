# User Roles and Access Control

## Overview
The Cooling Monitor application has two user roles with different access levels:

### Admin Role
Full access to all features:
- ✅ View dashboard
- ✅ View and respond to alerts
- ✅ Add, edit, and delete heat exchangers
- ✅ Create, edit, and delete users
- ✅ Configure application settings (Redfish credentials, SMTP, Teams)
- ✅ Access user management page

### Technician Role
Limited access for monitoring and alert response:
- ✅ View dashboard
- ✅ View and respond to alerts (acknowledge, resolve, comment)
- ❌ Cannot add/edit/delete heat exchangers
- ❌ Cannot access user management
- ❌ Cannot access settings page

## Protected Routes

### Admin-Only Pages
- `/heat-exchanger-form` - Add/Edit heat exchangers
- `/users` - User management
- `/settings` - Application settings

### Admin-Only API Endpoints
**Heat Exchangers:**
- `POST /api/heat-exchangers/` - Create heat exchanger
- `PUT /api/heat-exchangers/{id}` - Update heat exchanger
- `DELETE /api/heat-exchangers/{id}` - Delete heat exchanger

**Users:**
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

**Settings:**
- `PUT /api/settings/redfish-credentials` - Update Redfish credentials
- `PUT /api/settings/smtp` - Update notification settings

### Public Endpoints (No Authentication)
- `GET /api/heat-exchangers/` - List heat exchangers
- `GET /api/heat-exchangers/{id}` - Get heat exchanger details
- `GET /api/monitoring/{id}` - Get monitoring data
- `GET /api/settings/redfish-credentials` - Get Redfish username (no password)
- `GET /api/settings/smtp` - Get SMTP settings (no password)

### Authenticated User Endpoints
**Alerts (All authenticated users):**
- `GET /api/alerts` - List alerts with filters
- `GET /api/alerts/count` - Count alerts
- `PUT /api/alerts/{id}/acknowledge` - Acknowledge alert
- `PUT /api/alerts/{id}/resolve` - Resolve alert
- `POST /api/alerts/{id}/comment` - Add comment to alert

**Authentication:**
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user info

## User Management

### Creating Users (Admin Only)
1. Navigate to **User Management** page
2. Click **+ Add User**
3. Enter username (3-50 characters)
4. Enter password (minimum 6 characters)
5. Select role: **Admin** or **Technician**
6. Click **Save User**

### Editing Users (Admin Only)
- Change password (optional - leave blank to keep current)
- Change role (cannot demote yourself from admin)
- Cannot change username (create new user instead)

### Deleting Users (Admin Only)
- Cannot delete yourself
- Confirmation required

## Security Features

### Authentication
- JWT token-based authentication
- HTTP-only cookies for secure token storage
- 24-hour token expiration
- Bcrypt password hashing

### Authorization
- Role-based access control (RBAC)
- Admin privilege checks on protected endpoints
- Frontend hides admin-only links from technicians
- Backend enforces all access control rules

### Password Security
- Minimum 6 characters required
- Bcrypt hashing with automatic salt generation
- Encrypted storage for SMTP passwords (Fernet encryption)

## Default Credentials

The application comes with a default admin user:
- **Username:** admin
- **Password:** (set during initial setup)

**Important:** Change the default password immediately after first login!

## UI Behavior by Role

### Admin View
Navigation shows:
- Dashboard
- Alerts (with count badge)
- Add Heat Exchanger
- Users
- Settings

Detail pages show:
- Edit button
- Delete button

### Technician View
Navigation shows:
- Dashboard
- Alerts (with count badge)

Detail pages show:
- Back button only
- No edit/delete buttons

## Implementation Details

### Database Schema
```sql
users table:
- id: INTEGER (primary key)
- username: STRING (unique, indexed)
- hashed_password: STRING
- is_admin: INTEGER (1=admin, 0=technician)
- created_at: DATETIME
```

### Role Check Functions

**Backend (Python):**
```python
from app.routers.auth import require_admin

# Protect endpoint with admin role
@router.post("/endpoint")
async def admin_only_endpoint(
    current_user: User = Depends(require_admin)
):
    # Only admins can access this
    pass
```

**Frontend (JavaScript):**
```javascript
// Check user role and show/hide admin links
async function checkUserRole() {
    const response = await fetch('/api/auth/me');
    if (response.ok) {
        const user = await response.json();
        if (user.is_admin) {
            // Show admin links
        }
    }
}
```

## Migration

The user roles system uses the existing `is_admin` field:
- `is_admin=1` → Admin role
- `is_admin=0` → Technician role

No database migration required if you already have the users table.

## Best Practices

### For Admins
1. Create individual accounts for each person
2. Assign technician role by default
3. Only grant admin role to trusted personnel
4. Regularly review user list
5. Remove users who no longer need access
6. Use strong passwords (minimum 12 characters recommended)

### For Technicians
1. Change your password on first login
2. Report any access issues to admins
3. Only acknowledge alerts you're actively working on
4. Add meaningful comments when resolving alerts
5. Log out when leaving your workstation

## Troubleshooting

### "Admin privileges required" error
- You're logged in as a technician
- Ask an admin to upgrade your account
- Or log in with an admin account

### Cannot see admin menu items
- Clear browser cache and reload
- Check you're logged in (not just session expired)
- Verify your role with admin: GET /api/auth/me

### Locked out (no admin access)
- Contact system administrator
- Database access required to reset admin password or promote user:
  ```sql
  UPDATE users SET is_admin = 1 WHERE username = 'username';
  ```

## API Response Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid input (username exists, weak password)
- `401 Unauthorized` - Not logged in or token expired
- `403 Forbidden` - Insufficient privileges (technician trying to access admin endpoint)
- `404 Not Found` - Resource doesn't exist
- `500 Internal Server Error` - Server error
