# SMTP Email Settings - Encrypted Database Storage

## ✅ What Was Implemented

Instead of storing the SMTP password in `.env` or Azure Key Vault, the application now:

1. **Stores SMTP settings in the database** (system_settings table)
2. **Encrypts the password** using Fernet encryption before storage
3. **Provides a web UI** to configure all email settings at `/settings`
4. **Automatically loads settings** from database when sending urgent alarms

## 🔐 Security Features

- **Password Encryption**: SMTP password is encrypted using Fernet (symmetric encryption)
- **Encryption Key**: Derived from `SECRET_KEY` in config.py using SHA256
- **Password Never Displayed**: UI never shows the saved password (like GitHub secrets)
- **Database-Only Storage**: Passwords never stored in .env or config files

## 📧 How to Configure

### Option 1: Web Interface (Recommended)
1. Navigate to **Settings** page in the web app
2. Scroll to **Email Alert Settings** section
3. Fill in the form:
   - ✅ Enable Email Alerts (checkbox)
   - **SMTP Server**: `smtp.office365.com`
   - **SMTP Port**: `587`
   - **Email Username**: `schielabintegration@microsoft.com`
   - **Email Password**: Your Outlook app password
   - **From Email**: `schielabintegration@microsoft.com`
   - **Recipients**: Comma-separated list of emails
   - ✅ Use TLS (checked)
   - **Flow Threshold**: `10.0` L/min
4. Click **Save Email Settings**
5. Password will be encrypted and stored in database

### Option 2: Database Direct (Advanced)
```python
from app.utils.encryption import encrypt_value
encrypted_password = encrypt_value("your-password")
# Then insert into database
```

## 📁 Files Modified

### New Files Created:
- `app/utils/encryption.py` - Encryption/decryption utilities
- `migrate_smtp_settings.py` - Database migration script

### Modified Files:
- `app/models/settings.py` - Added SMTP columns and schemas
- `app/routers/settings.py` - Added `/api/settings/smtp` endpoints
- `app/services/email_service.py` - Now reads from database with decryption
- `app/services/monitoring_service.py` - Passes db session to email service
- `app/config.py` - Removed Azure Key Vault code
- `requirements.txt` - Added cryptography package
- `templates/settings.html` - Added SMTP settings form
- `static/js/settings.js` - Added SMTP form handling

## 🔄 How It Works

1. **User enters password** in web UI
2. **Frontend sends** to `/api/settings/smtp` endpoint
3. **Backend encrypts** password using Fernet
4. **Stores encrypted** value in database
5. **On alarm trigger**, monitoring service:
   - Queries database for SMTP settings
   - Decrypts password
   - Sends email via SMTP
   - Never logs decrypted password

## 🚀 Next Steps

1. Configure SMTP settings via web UI
2. Test with a pump flow < 10 L/min (or adjust threshold)
3. Verify email is received
4. Check console logs for "✅ Urgent alarm email sent"

## 🔒 Security Notes

- **SECRET_KEY** in config.py must remain secret (used for encryption)
- Changing SECRET_KEY will invalidate all encrypted passwords
- Database file should have restricted file permissions in production
- HTTPS recommended for production deployment (protects password in transit)

## 📋 Microsoft 365 Setup

For `schielabintegration@microsoft.com`:
1. Enable MFA if not already enabled
2. Go to https://account.microsoft.com/security
3. Create **App Password** (under Security info)
4. Use app password (not regular password) in SMTP settings
5. Use `smtp.office365.com` server on port 587

## ✅ Migration Status

- Database columns already exist (checked via migration script)
- Ready to use immediately after configuration
