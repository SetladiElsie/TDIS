# Email Notifications - Quick Start

## Status: Optional Feature ✅

The TDIS system works perfectly **without** email configuration. This feature is optional and enhances the user experience.

---

## Current State

🟡 **Email: DISABLED** (not configured)

- ✅ System fully functional
- ✅ Admins see temporary passwords in UI
- ✅ Admins share passwords manually

---

## Quick Enable (Gmail - 5 minutes)

### Step 1: Get App Password
1. Visit: https://myaccount.google.com/apppasswords
2. Enable 2FA if not already enabled
3. Generate app password
4. Copy the 16-character code

### Step 2: Configure
Create or edit `.env` file:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=abcdefghijklmnop
MAIL_FROM=noreply@tia-solutions.co.za
```

### Step 3: Restart
```bash
# Stop backend (Ctrl+C in terminal)
# Start again
python app.py
```

### Step 4: Test
```bash
python test_email.py
```

---

## What Happens When Enabled

### Creating New User
**Before:** Admin copies temp password from UI → sends to user manually
**After:** Admin creates user → email sent automatically ✉️

### Resetting Password
**Before:** Admin copies new temp password → sends to user manually
**After:** Admin resets password → email sent automatically ✉️

---

## Email Template Preview

```
┌─────────────────────────────────────────┐
│                                         │
│         TIA Solutions                   │
│   Technology Infrastructure Architects  │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Welcome, John!                         │
│                                         │
│  Your account has been created by       │
│  Admin Name for the Tender Extraction   │
│  Portal.                                │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Email / Username                │   │
│  │ john@example.com                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Temporary Password              │   │
│  │ Temp7kL2v!3xZ1!                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ⚠️ Security Notice:                    │
│  You must change this password on       │
│  your first login.                      │
│                                         │
│  [ Login to Portal ]                    │
│                                         │
└─────────────────────────────────────────┘
```

---

## Production Setup (SendGrid)

**Why SendGrid?**
- ✅ Better deliverability
- ✅ 100 free emails/day
- ✅ Professional service
- ✅ Delivery tracking

**Setup:**
1. Sign up: https://sendgrid.com
2. Create API key
3. Add to Render environment:
   ```
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=SG.your_api_key
   MAIL_FROM=noreply@tia-solutions.co.za
   ```

---

## Troubleshooting

### "Email service is DISABLED"
→ Add MAIL_* variables to `.env`
→ Restart backend

### "Authentication failed"
→ Gmail: Use App Password, not regular password
→ Check username/password correct

### "Email not received"
→ Check spam/junk folder
→ Run `python test_email.py`
→ Check logs: `cat logs/app.log | grep email`

---

## Need More Help?

📖 **Detailed Guide:** `EMAIL_SETUP_GUIDE.md` (25 pages)
🧪 **Test Script:** `python test_email.py`
📋 **Implementation Details:** See artifact "Email Notifications Feature - Complete Summary"

---

## Bottom Line

✅ **Optional feature - system works perfectly without it**
✅ **5-minute setup with Gmail**
✅ **Professional branded emails with TIA Solutions theme**
✅ **Automatic notifications on user creation and password reset**
✅ **Graceful fallback if email fails**

**To enable:** Add 5 lines to `.env`, restart, done! 🚀
