# Microsoft Teams Notifications Setup Guide

## ✅ What's Available Now

The application now supports **Microsoft Teams webhook notifications** as an alternative to email alerts when SMTP authentication is blocked by your organization.

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Incoming Webhook in Teams

1. Open Microsoft Teams
2. Go to the channel where you want to receive alerts
3. Click the **...** (More options) next to the channel name
4. Select **Workflows** or **Connectors**
5. Search for **"Incoming Webhook"**
6. Click **Add** or **Configure**
7. Name it: `Cooling Monitor Alerts`
8. Optional: Upload an icon
9. Click **Create**
10. **Copy the webhook URL** (starts with `https://outlook.office.com/webhook/...`)

### Step 2: Configure in Application

1. Go to **Settings** page in the web app (http://localhost:8000/settings)
2. Scroll to **"Microsoft Teams Notifications"** section
3. Check **"Enable Teams Notifications"**
4. Paste the webhook URL
5. Set your pump flow threshold (default: 10.0 L/min)
6. Click **"Save Notification Settings"**

### Step 3: Test It

Run the test script:
```powershell
python test_teams.py
```

You should see a blue test message in your Teams channel!

## 📧 Email vs Teams Comparison

| Feature | Email (SMTP) | Teams Webhook |
|---------|--------------|---------------|
| **Setup Difficulty** | Hard (auth issues) | Easy (5 minutes) |
| **Requires Password** | Yes (app password) | No |
| **Org Restrictions** | Often blocked | Usually allowed |
| **Real-time** | ~1-2 minutes | Instant |
| **Formatting** | Plain text | Rich cards |
| **Mobile Notifications** | Yes | Yes (if Teams installed) |

## 🎨 What Urgent Alarms Look Like in Teams

When a pump flow rate drops below the threshold, you'll receive a rich adaptive card with:

- **Red theme** for urgency
- Heat exchanger name
- Pump ID
- Current flow rate (highlighted)
- Critical threshold
- Timestamp
- Action required message

## 🔧 How It Works

1. **Monitoring service** polls pump status every 30 seconds
2. **Detects** flow rate < threshold (default: 10 L/min)
3. **Sends** to Teams webhook (and/or email if both enabled)
4. **Teams** delivers instantly to channel

## ✅ Advantages Over Email

- ✅ **No authentication issues** - bypasses SMTP blocks
- ✅ **No app passwords needed** - just a webhook URL
- ✅ **Instant delivery** - no SMTP delays
- ✅ **Rich formatting** - adaptive cards with colors
- ✅ **Channel history** - searchable alarm log
- ✅ **@mentions possible** - can notify specific people (with webhook customization)

## 🎯 Can I Use Both?

Yes! You can enable both Teams and Email notifications:

- **Teams**: Instant alerts for on-call team
- **Email**: For audit trail and people without Teams

## 🔒 Security Notes

- Webhook URL is stored in database (not encrypted - it's not a password)
- Anyone with the webhook URL can post to your channel
- Treat the webhook URL like a password
- You can revoke/regenerate webhooks in Teams at any time

## 📱 Mobile Notifications

If team members have Teams mobile app:
1. They'll receive push notifications
2. Can view rich card on mobile
3. Can respond immediately

## 🛠️ Troubleshooting

**"Teams notifications are DISABLED"**
- Enable checkbox in Settings page

**"No webhook URL configured"**
- Create webhook in Teams and paste URL in Settings

**"Failed to send Teams message"**
- Verify webhook URL is correct
- Check if webhook was deleted in Teams
- Ensure webhook hasn't expired

**"HTTP 400 error"**
- Webhook URL format is invalid
- Copy the entire URL including all query parameters

## 📋 Test Scripts Available

- `test_teams.py` - Test Teams webhook
- `test_email.py` - Test email SMTP

Run both to verify your notification setup!

## 🎉 Recommendation

**Use Teams webhooks** if your organization blocks SMTP authentication. It's simpler, faster, and doesn't require dealing with passwords or authentication issues.

You're all set! Configure your webhook and you'll receive instant Teams notifications when pump flow rates drop critically low.
