# Email Configuration Guide for TDIS

This guide explains how to set up email notifications for temporary passwords and password resets in the Tender Document Information System.

## Overview

When email is configured, the system will automatically:
- ✉️ Email temporary passwords to new users when admins create their accounts
- ✉️ Email new temporary passwords when admins reset user passwords
- 🎨 Send professional HTML emails with TIA Solutions branding

If email is **not configured**, the system will still work - admins will see the temporary passwords in the UI and can share them manually.

---

## Quick Start (Gmail)

### 1. Enable 2-Factor Authentication on Gmail
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification

### 2. Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and your device
3. Click "Generate"
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### 3. Configure Environment Variables

Add these to your `.env` file:

```bash
# Gmail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=abcdefghijklmnop  # App password (no spaces)
MAIL_FROM=noreply@tia-solutions.co.za
```

### 4. Restart the Application

```bash
# Stop the current backend
# Ctrl+C in the terminal running app.py

# Restart
python app.py
```

---

## Alternative Email Providers

### SendGrid (Recommended for Production)

**Why SendGrid?**
- Free tier: 100 emails/day
- Better deliverability than Gmail
- Professional email service

**Setup:**

1. Sign up at [SendGrid.com](https://sendgrid.com/)
2. Create an API key
3. Configure:

```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey  # Literally "apikey"
MAIL_PASSWORD=SG.your_api_key_here
MAIL_FROM=noreply@tia-solutions.co.za
```

### Mailgun

**Setup:**

1. Sign up at [Mailgun.com](https://www.mailgun.com/)
2. Get SMTP credentials
3. Configure:

```bash
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=your-mailgun-username
MAIL_PASSWORD=your-mailgun-password
MAIL_FROM=noreply@tia-solutions.co.za
```

### Microsoft 365 / Outlook

```bash
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
MAIL_FROM=your-email@outlook.com
```

### Custom SMTP Server

```bash
MAIL_SERVER=smtp.yourdomain.com
MAIL_PORT=587  # or 465 for SSL
MAIL_USERNAME=username
MAIL_PASSWORD=password
MAIL_FROM=noreply@yourdomain.com
```

---

## Configuration Options

All email settings are optional. The system will detect if email is configured and enable/disable accordingly.

| Variable | Default | Description |
|----------|---------|-------------|
| `MAIL_SERVER` | None | SMTP server hostname |
| `MAIL_PORT` | 587 | SMTP port (587 for TLS, 465 for SSL) |
| `MAIL_USERNAME` | None | SMTP username |
| `MAIL_PASSWORD` | None | SMTP password or API key |
| `MAIL_FROM` | `tdis-no-reply@tia-solutions.co.za` | From email address |

---

## Testing Email Configuration

### Test via Python

Create a test script `test_email.py`:

```python
from app import create_app
from email_service import get_email_service

app = create_app('development')

with app.app_context():
    email_service = get_email_service()
    
    if email_service and email_service.enabled:
        print("✅ Email service is ENABLED")
        
        # Send test email
        success = email_service.send_email(
            to_email='your-email@example.com',
            subject='Test Email from TDIS',
            html_body='<h1>Test successful!</h1><p>Email is working.</p>'
        )
        
        if success:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email")
    else:
        print("⚠️ Email service is DISABLED (not configured)")
```

Run:
```bash
python test_email.py
```

### Test via UI

1. Log in as admin
2. Go to User Management
3. Create a new user with temporary password checkbox
4. Check:
   - ✅ Temporary password appears in UI
   - ✅ Email is sent to user (if configured)
   - ✅ Check application logs for email status

---

## Email Templates

The system sends two types of emails:

### 1. New User Welcome Email

Sent when admin creates a user with temporary password.

**Contains:**
- Welcome message
- Login credentials (email + temporary password)
- Security notice about changing password
- Link to login portal
- TIA Solutions branding

### 2. Password Reset Email

Sent when admin resets a user's password.

**Contains:**
- Password reset notification
- New temporary password
- Security warning
- Link to login portal
- TIA Solutions branding

---

## Production Deployment (Render)

### Environment Variables in Render

1. Go to your backend service in Render dashboard
2. Navigate to **Environment** tab
3. Add email variables:

```
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.your_api_key
MAIL_FROM=noreply@tia-solutions.co.za
```

4. Save changes - Render will automatically redeploy

### Update Login URL in Emails

Before deploying, update `email_service.py` to use your production URL:

```python
# Replace localhost with your production URL
# http://localhost:3000 → https://your-app.onrender.com

<a href="https://your-app.onrender.com" class="button">Login to Portal</a>
```

---

## Troubleshooting

### Email not sending

**Check logs:**
```bash
# Look for email-related log messages
cat logs/app.log | grep -i email
```

**Common issues:**

1. **"Email service is DISABLED"**
   - Check `.env` file has all required variables
   - Restart the application after changes

2. **"Authentication failed"**
   - Gmail: Use App Password, not regular password
   - Check username/password are correct
   - Verify 2FA is enabled (Gmail)

3. **"Connection refused"**
   - Check `MAIL_SERVER` hostname is correct
   - Verify `MAIL_PORT` (587 for TLS, 465 for SSL)
   - Check firewall/network settings

4. **"Emails not received"**
   - Check spam/junk folder
   - Verify `MAIL_FROM` email address
   - Test with a different recipient
   - Check SendGrid/Mailgun dashboard for delivery status

### Testing without email

The system works perfectly without email configured. Temporary passwords will:
- ✅ Appear in the admin UI after creation/reset
- ✅ Be stored in browser session
- ✅ Be visible via "View Password" button
- ✅ Be logged in application logs (INFO level)

---

## Security Best Practices

### ✅ DO:
- Use App Passwords for Gmail (not your real password)
- Use environment variables (never hardcode passwords)
- Use dedicated "noreply" or "notifications" email addresses
- Use SendGrid/Mailgun for production (better deliverability)
- Keep `.env` file out of git (already in `.gitignore`)

### ❌ DON'T:
- Commit passwords to git
- Use your personal email password
- Share App Passwords
- Send emails with real passwords over unencrypted connections
- Store sensitive credentials in code

---

## Features Implemented

✅ **Automatic email sending** when admin creates user with temp password
✅ **Automatic email sending** when admin resets user password
✅ **HTML email templates** with TIA Solutions branding
✅ **Graceful fallback** - works without email configuration
✅ **Multiple provider support** - Gmail, SendGrid, Mailgun, etc.
✅ **Error handling** - email failures don't break user creation
✅ **Logging** - all email activity is logged

---

## Support

If you need help:
1. Check the logs: `logs/app.log`
2. Verify `.env` configuration
3. Test with the test script above
4. Check your email provider's documentation
5. Review Render deployment logs (if deployed)

---

**Last Updated:** January 2025
**Version:** 1.0
**Author:** TIA Solutions
