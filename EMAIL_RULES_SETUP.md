# Email Rules Setup Guide (cPanel / CubeSquare)

## Overview

This guide shows how to set up email rules in cPanel or CubeSquare for two types of emails:

### 1. Telemetry/Log Emails
- **From**: `support@moviolabs.com` (application)
- **To**: `telemetry@moviolabs.com`
- **Purpose**: Telemetry data, session logs, and application diagnostics

### 2. License Requests
- **From**: Users (e.g., `@hfmdd.de` accounts)
- **To**: `support@moviolabs.com`
- **Purpose**: License key requests and support inquiries

---

## 🎯 Priority Setup: Auto-Send License to @hfmdd.de Accounts

### Goal
Automatically send a license immediately when an email arrives from any `@hfmdd.de` account.

### Method 1: Email Filter + Autoresponder (Recommended - No Code)

This uses cPanel's built-in features - no code required!

#### Step 1: Set Up Email Filter

1. In cPanel, go to **Email** → **Email Filters**
2. Select account: **support@moviolabs.com** (the account receiving license requests)
3. Click **Create a New Filter**
4. **Filter Name**: `Auto-License for HFMDD`
5. **Rules**:
   - **Match**: `From` contains `@hfmdd.de`
   - **Action**: 
     - ✅ Deliver to folder: `Licenses/HFMDD` (optional - for tracking)
     - ✅ Forward to: `support@moviolabs.com` (optional - for notification)

#### Step 2: Set Up Autoresponder

1. In cPanel, go to **Email** → **Autoresponders**
2. Click **Add Autoresponder**
3. **Email**: Select `support@moviolabs.com` (the license request email)
4. **Name**: `HFMDD Auto-License`
5. **Rules**:
   - **From**: Contains `@hfmdd.de`
   - **Subject**: (leave blank or set to match license requests)
6. **Body**: Copy and paste this template:

```
Subject: Your MVC Calculator License Key

Dear Customer,

Thank you for your request. Your license key is attached.

Please save the attached license.key file to:
  Windows: %APPDATA%\MVC_Calculator\license.key

If you need assistance, please contact support@moviolabs.com

Best regards,
MVC Calculator Support
```

7. **Attachments**: (Optional) You can attach a generic license file, but for personalized licenses, see Method 2 below.

8. **Enable**: ✅ Check "Enable Autoresponder"
9. Click **Create**

### Method 2: Forward to License Generation Script (For Dynamic Licenses)

If you need to generate unique licenses based on the sender's email address, you'll need a script. However, you can still use email rules to trigger it:

1. **Set up Email Filter** (same as Method 1, Step 1)
2. **Add Forward Action**: Forward emails from `@hfmdd.de` to a script that:
   - Extracts the sender's email
   - Generates a license using `generate_license.py`
   - Emails the license back to the sender

**Note**: This requires a server-side script (PHP/Python) that can be triggered via email or webhook.

### Method 3: Simple Autoresponder Only (Quickest)

If you just want to send a pre-generated license file:

1. **Email** → **Autoresponders**
2. **Add Autoresponder**
3. **From**: Contains `@hfmdd.de`
4. **Attach File**: Upload your `license.key` file
5. **Body**: Instructions on where to place the license file
6. **Enable** and **Create**

### Testing

1. Send a test email from any `@hfmdd.de` address to `support@moviolabs.com`
2. Check that the autoresponder triggers immediately
3. Verify the license email is received

### Important Notes

- ⚠️ **Autoresponders send to ALL emails matching the rule** - make sure your "From" filter is specific
- ⚠️ **For unique licenses per user**, you'll need Method 2 with a script
- ✅ **Autoresponders work immediately** - no delay
- ✅ **No code required** for Method 1 and Method 3

---

## Option A: cPanel Email Filters

### Quick Start - Which Option to Use?

Based on your cPanel interface, you have **three main options**:

1. **📧 Email Filters** (Funnel icon with envelope)
   - **Best for**: Account-specific rules for `telemetry@moviolabs.com`
   - **Use this for**: Filtering, organizing, and forwarding emails to this specific account

2. **🌐 Global Email Filters** (Funnel icon with globe)
   - **Best for**: System-wide rules that apply to ALL email accounts
   - **Use this for**: Rules that should apply to every email on your domain

3. **➡️ Forwarders** (Arrow icon with envelope)
   - **Best for**: Simple forwarding without conditions
   - **Use this for**: Just forwarding all emails from `telemetry@moviolabs.com` to another address

**Recommendation**: Start with **Email Filters** for the most flexibility.

### Step 1: Access Email Filters

1. In the **Email** section (you're already here!), click **Email Filters** (the funnel icon with a small orange envelope)
2. This will show filters for your email accounts

### Step 2: Create a New Filter

1. Click **Create a New Filter**
2. Select the email account: **telemetry@moviolabs.com**
3. Give the filter a name: `Telemetry Auto-Organize`

### Step 3: Configure Filter Rules

**Rule 1: Forward Telemetry Emails**
- **Match**: `From` contains `support@moviolabs.com`
- **Action**: 
  - Forward to: `your-email@moviolabs.com` (or your support email)
  - **OR** Deliver to folder: `Telemetry` (create folder first)

**Rule 2: Archive by Subject**
- **Match**: `Subject` contains `Telemetry` OR `Session Log`
- **Action**: Deliver to folder: `Telemetry/Logs`

**Rule 3: Auto-Reply (Optional)**
- **Match**: `To` equals `telemetry@moviolabs.com`
- **Action**: 
  - Send auto-reply: "Telemetry received. Thank you."
  - **AND** Deliver to folder: `Telemetry/Received`

### Step 4: Advanced Rules (Multiple Conditions)

For more complex filtering:

**Example: Organize by Attachment Type**
- **Match**: 
  - `From` contains `support@moviolabs.com`
  - **AND** `Has Attachments` is `Yes`
- **Action**: Deliver to folder: `Telemetry/WithAttachments`

**Example: Priority Filtering**
- **Match**: 
  - `Subject` contains `ERROR` OR `CRITICAL`
- **Action**: 
  - Forward to: `support@moviolabs.com`
  - **AND** Mark as important
  - **AND** Deliver to folder: `Telemetry/Priority`

---

## Alternative: Simple Forwarding (Easiest Option)

If you just want to forward all emails from `telemetry@moviolabs.com` to another address without any conditions:

1. In the **Email** section, click **Forwarders** (arrow icon with envelope)
2. Click **Add Forwarder**
3. Select: **telemetry@moviolabs.com**
4. Forward to: `your-email@moviolabs.com` (or your support email)
5. Click **Add Forwarder**

That's it! All emails to `telemetry@moviolabs.com` will be automatically forwarded.

---

## Alternative: Simple Forwarding (Easiest Option)

If you just want to forward all emails from `telemetry@moviolabs.com` to another address without any conditions:

1. In the **Email** section, click **Forwarders** (arrow icon with envelope)
2. Click **Add Forwarder**
3. Select: **telemetry@moviolabs.com**
4. Forward to: `your-email@moviolabs.com` (or your support email)
5. Click **Add Forwarder**

That's it! All emails to `telemetry@moviolabs.com` will be automatically forwarded.

---

## Option B: CubeSquare Email Rules

### Step 1: Access Email Management

1. Log into **CubeSquare** control panel
2. Navigate to **Email** → **Email Accounts**
3. Click on **telemetry@moviolabs.com**
4. Click **Email Filters** or **Rules**

### Step 2: Create Filter Rule

1. Click **Add Filter** or **New Rule**
2. Configure the rule:

**Basic Rule:**
- **Name**: `Telemetry Forward`
- **If**: 
  - Field: `From`
  - Condition: `Contains`
  - Value: `support@moviolabs.com`
- **Then**:
  - Action: `Forward to`
  - Address: `your-email@moviolabs.com`
  - **OR** Action: `Move to Folder`
  - Folder: `Telemetry`

### Step 3: Multiple Actions

You can chain multiple actions:

**Example: Forward and Archive**
- **If**: `From` contains `support@moviolabs.com`
- **Then**:
  1. Forward to: `support@moviolabs.com`
  2. Move to folder: `Telemetry/Archive`
  3. Mark as read (optional)

---

## Recommended Setup

### Scenario 1: Simple Forwarding

**Goal**: Forward all telemetry emails to your main support inbox

**cPanel/CubeSquare Rule:**
```
IF: From contains "@hfmdd.de"
AND: To equals "support@moviolabs.com"
THEN: Forward to "support@moviolabs.com" (or trigger license generation)
```

### Scenario 2: Organized Storage

**Goal**: Organize telemetry emails into folders for easy access

**Rules:**
1. **All Telemetry** → Move to folder: `Telemetry/All`
2. **With Attachments** → Move to folder: `Telemetry/Logs`
3. **Error Reports** → Move to folder: `Telemetry/Errors` + Forward to support

### Scenario 3: Auto-Archive

**Goal**: Archive old telemetry emails automatically

**Rule:**
```
IF: From contains "support@moviolabs.com"
AND: Date is older than 30 days
THEN: Move to folder "Telemetry/Archive"
```

---

## Common Use Cases

### 1. Forward Critical Errors

**Rule:**
- **Match**: `Subject` contains `ERROR` OR `CRITICAL` OR `FAILED`
- **Action**: Forward to `support@moviolabs.com` immediately

### 2. Separate Log Files

**Rule:**
- **Match**: `Has Attachments` is `Yes`
- **Action**: Move to folder `Telemetry/LogFiles`

### 3. Daily Digest

**Rule:**
- **Match**: `From` contains `support@moviolabs.com`
- **Action**: 
  - Forward to `support@moviolabs.com`
  - Move to folder `Telemetry/Daily`

### 4. Spam Protection

**Rule:**
- **Match**: `From` does NOT contain `support@moviolabs.com`
- **Action**: Move to folder `Spam` or delete

---

## Testing Your Rules

1. **Send a test email** from any `@hfmdd.de` address to `support@moviolabs.com`
2. **Check** if the rule triggers correctly
3. **Verify** the email appears in the expected folder/location
4. **Adjust** the rule if needed

---

## Troubleshooting

### Rule Not Working?

1. **Check rule order**: Rules are processed top-to-bottom. Move your rule higher if needed.
2. **Verify syntax**: Ensure email addresses match exactly (case-sensitive in some systems)
3. **Test conditions**: Use simple conditions first, then add complexity
4. **Check folder exists**: Create folders before assigning emails to them

### Email Not Arriving?

1. **Check spam folder**: Rules might be moving emails there
2. **Verify forwarding**: Ensure forwarding address is correct
3. **Check quota**: Mailbox might be full
4. **Review logs**: Check email logs in cPanel/CubeSquare for delivery issues

---

## Best Practices

1. **Start Simple**: Create one rule at a time and test it
2. **Use Folders**: Organize emails into folders for easy management
3. **Set Limits**: Consider auto-deleting emails older than 90 days
4. **Monitor**: Check the telemetry mailbox periodically to ensure rules work
5. **Backup**: Important telemetry data should be forwarded or archived

---

## Notes

- **No Code Required**: All of this is done through the web interface
- **Server-Side**: Rules run on the mail server, so they work even if the application is offline
- **Automatic**: Once set up, rules run automatically for all incoming emails
- **Reversible**: You can disable or delete rules at any time

---

## Support

For issues with email rules setup:
- **cPanel**: Check cPanel documentation or contact your hosting provider
- **CubeSquare**: Check CubeSquare documentation or contact support
- **Application**: Contact support@moviolabs.com

