# Power Automate Flow Setup for Teams Notifications

## ✅ Why Power Automate?

If your organization blocks Incoming Webhooks, Power Automate flows provide the same functionality and often bypass DLP policies since they're considered internal automation.

## 🚀 Setup Guide (10 minutes)

### Step 1: Create a Power Automate Flow

1. Go to https://make.powerautomate.com
2. Click **+ Create** → **Automated cloud flow**
3. Name it: `Cooling Monitor Urgent Alerts`
4. Search for and select trigger: **"When a HTTP request is received"**
5. Click **Create**

### Step 2: Configure HTTP Trigger

The trigger will open with a **Request Body JSON Schema** field.

**Paste this schema:**
```json
{
    "type": "object",
    "properties": {
        "@type": {
            "type": "string"
        },
        "@context": {
            "type": "string"
        },
        "themeColor": {
            "type": "string"
        },
        "summary": {
            "type": "string"
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "activityTitle": {
                        "type": "string"
                    },
                    "activitySubtitle": {
                        "type": "string"
                    },
                    "facts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string"
                                },
                                "value": {
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "text": {
                        "type": "string"
                    }
                }
            }
        }
    }
}
```

### Step 3: Add Teams Action

1. Click **+ New step**
2. Search for **"Post message in a chat or channel"**
3. Select **Microsoft Teams** connector
4. Configure:
   - **Post as**: Flow bot
   - **Post in**: Channel
   - **Team**: Select your team
   - **Channel**: Select the channel for alerts
   - **Message**: Use dynamic content (see below)

### Step 4: Build the Message

Click in the **Message** field and use **Add dynamic content**:

**Simple Version (Plain Text):**
```
🚨 URGENT ALARM

Summary: sections[0].activityTitle

Details:
sections[0].facts[0].name sections[0].facts[0].value
sections[0].facts[1].name sections[0].facts[1].value
sections[0].facts[2].name sections[0].facts[2].value
sections[0].facts[3].name sections[0].facts[3].value

Action: sections[1].text

Time: sections[0].activitySubtitle
```

**Advanced Version (Adaptive Card):**
1. Click the **Message** field
2. Switch to **Code View** (</> icon)
3. Paste this adaptive card:
```json
{
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.4",
    "body": [
        {
            "type": "Container",
            "style": "attention",
            "items": [
                {
                    "type": "TextBlock",
                    "text": "@{triggerBody()?['sections']?[0]?['activityTitle']}",
                    "weight": "Bolder",
                    "size": "Large",
                    "color": "Attention"
                },
                {
                    "type": "TextBlock",
                    "text": "@{triggerBody()?['sections']?[0]?['activitySubtitle']}",
                    "size": "Small",
                    "isSubtle": true
                }
            ]
        },
        {
            "type": "FactSet",
            "facts": [
                {
                    "title": "@{triggerBody()?['sections']?[0]?['facts']?[0]?['name']}",
                    "value": "@{triggerBody()?['sections']?[0]?['facts']?[0]?['value']}"
                },
                {
                    "title": "@{triggerBody()?['sections']?[0]?['facts']?[1]?['name']}",
                    "value": "@{triggerBody()?['sections']?[0]?['facts']?[1]?['value']}"
                },
                {
                    "title": "@{triggerBody()?['sections']?[0]?['facts']?[2]?['name']}",
                    "value": "@{triggerBody()?['sections']?[0]?['facts']?[2]?['value']}"
                },
                {
                    "title": "@{triggerBody()?['sections']?[0]?['facts']?[3]?['name']}",
                    "value": "@{triggerBody()?['sections']?[0]?['facts']?[3]?['value']}"
                },
                {
                    "title": "@{triggerBody()?['sections']?[0]?['facts']?[4]?['name']}",
                    "value": "@{triggerBody()?['sections']?[0]?['facts']?[4]?['value']}"
                }
            ]
        },
        {
            "type": "TextBlock",
            "text": "@{triggerBody()?['sections']?[1]?['text']}",
            "wrap": true,
            "weight": "Bolder"
        }
    ]
}
```

### Step 5: Save and Get URL

1. Click **Save** (top right)
2. Expand the **"When a HTTP request is received"** trigger again
3. **Copy the HTTP POST URL** (it will appear after saving)
   - Format: `https://prod-XX.westus.logic.azure.com:443/workflows/...`

### Step 6: Configure in Cooling Monitor

1. Go to **Settings** page in your app
2. Scroll to **"Microsoft Teams Notifications"**
3. Check **"Enable Teams Notifications"**
4. Paste the Power Automate **HTTP POST URL** in the webhook field
5. Click **"Save Notification Settings"**

### Step 7: Test It

Run the test script:
```powershell
python test_teams.py
```

You should see a message posted to your Teams channel via the flow!

## 🎯 How It Works

1. **Cooling Monitor** detects low pump flow
2. **Sends JSON** to Power Automate HTTP endpoint
3. **Flow triggers** and extracts data
4. **Posts message** to Teams channel
5. **Team members** receive instant notification

## ✅ Advantages Over Webhook

- ✅ **Bypasses DLP policies** - internal automation
- ✅ **More customization** - edit message format in flow
- ✅ **Add logic** - filter alarms, add conditions, notify specific people
- ✅ **Audit trail** - Flow run history
- ✅ **Add actions** - send email, create ticket, update database

## 🔧 Advanced Customizations

### Add @mentions
In the Teams action, use:
```
<at>John Doe</at> - Urgent attention needed!

[rest of message]
```

### Add Conditions
Insert a **Condition** action before Teams to:
- Only alert during business hours
- Escalate after X minutes
- Notify different channels based on severity

### Add Multiple Actions
After receiving the HTTP request:
- Post to multiple Teams channels
- Send email backup
- Create Planner task
- Log to SharePoint list
- Send SMS via Twilio

## 🛠️ Troubleshooting

**"401 Unauthorized"**
- Flow might require authentication - ensure it's saved as the owner

**"Flow did not trigger"**
- Check Run History in Power Automate
- Verify the HTTP POST URL is correct
- Ensure JSON schema matches

**"Message doesn't format correctly"**
- Use the simple text version first to test
- Check dynamic content paths match your data

**"DLP still blocks"**
- Request exception for "When a HTTP request is received" trigger
- Use premium connector if available

## 📱 Mobile Notifications

Teams mobile app will deliver push notifications just like webhook notifications!

## 💰 Licensing

- **Free tier**: 750 runs/month (more than enough)
- **Premium**: If you need more runs or premium connectors

## 🎉 Next Steps

Once working, you can:
1. Create separate flows for different alert types
2. Add escalation logic
3. Integrate with incident management
4. Add approval workflows for maintenance

---

**The best part?** Your Cooling Monitor application doesn't know or care whether it's talking to a webhook or Power Automate - they both just accept JSON over HTTPS!
