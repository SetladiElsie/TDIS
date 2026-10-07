# 🔒 File Security Setup Guide

## Overview

This guide covers setting up advanced file security features for TDIS:
- **MIME Type Validation** - Prevents file extension spoofing
- **Virus Scanning** - Detects malware in uploaded files
- **Secure Storage** - Files stored outside web root

---

## 📦 Step 1: Install Required Dependencies

### Python Packages

```bash
# Navigate to project directory
cd "c:\Users\ElsieSetladi\Demo TDIS\TDIS"

# Activate virtual environment
.\.venv\Scripts\activate

# Install security packages
pip install python-magic python-magic-bin clamd
```

**Packages installed:**
- `python-magic` - MIME type detection from file content
- `python-magic-bin` - Windows binaries for python-magic
- `clamd` - Python interface for ClamAV antivirus

---

## 🦠 Step 2: Install ClamAV (Antivirus)

### Windows

**Option A: Using Chocolatey (Recommended)**
```powershell
# Install Chocolatey if not installed
# Visit: https://chocolatey.org/install

# Install ClamAV
choco install clamav
```

**Option B: Manual Installation**
1. Download from: https://www.clamav.net/downloads
2. Install to: `C:\Program Files\ClamAV`
3. Add to PATH: `C:\Program Files\ClamAV\bin`

**Start ClamAV Daemon:**
```powershell
# Option 1: Run as service
clamd

# Option 2: Run in background
Start-Process clamd -WindowStyle Hidden
```

### Linux (Ubuntu/Debian)

```bash
# Install ClamAV
sudo apt-get update
sudo apt-get install clamav clamav-daemon

# Start the daemon
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon

# Check status
sudo systemctl status clamav-daemon
```

### macOS

```bash
# Install with Homebrew
brew install clamav

# Start the service
brew services start clamav
```

---

## 🔄 Step 3: Update Virus Definitions

**CRITICAL:** Update virus definitions before first use

### Windows
```powershell
freshclam
```

### Linux/macOS
```bash
sudo freshclam
```

**Expected Output:**
```
ClamAV update process started at...
Downloading main.cvd [100%]
Downloading daily.cvd [100%]
Downloading bytecode.cvd [100%]
```

**Note:** This may take 5-15 minutes on first run

---

## ⚙️ Step 4: Configure Environment Variables

Update your `.env` file:

```env
# ── File Security ─────────────────────────────────────────────────────────────
# Enable MIME type validation (prevents file extension spoofing)
ENABLE_FILE_MIME_VALIDATION=True

# Enable virus scanning with ClamAV
ENABLE_VIRUS_SCANNING=True

# Production: Use absolute path outside web root
# UPLOAD_FOLDER=/var/uploads/tdis/
# Development: Use relative path
UPLOAD_FOLDER=uploads/

# Quarantine folder for suspicious files
QUARANTINE_FOLDER=quarantine/
```

---

## ✅ Step 5: Test Installation

Run the diagnostic test script:

```powershell
# Activate virtual environment
.\.venv\Scripts\activate

# Run diagnostic test
python file_security.py
```

**Expected Output:**
```
🔒 TDIS File Security Module - Diagnostic Test

1. Testing MIME Type Detection:
✅ python-magic installed
✅ Magic instance created

2. Testing Virus Scanning (ClamAV):
✅ ClamAV is available and running

3. Testing File Validation:
Testing with file: README.md
  Detected MIME type: text/plain
  
Validation Result:
  Valid: False (expected - README not in allowed types)
  MIME Type: text/plain
  Virus Scanned: True
  Virus Found: False

Summary:
  MIME Type Validation: ✅ Available
  Virus Scanning: ✅ Available

🎉 All security features are operational!
```

---

## 🚀 Step 6: Integration with Application

The security features are automatically integrated when enabled in `.env`.

### How It Works

**1. File Upload:**
```python
# In routes.py
from file_security import validate_file_security

# After saving uploaded file
result = validate_file_security(file_path, filename)

if not result['valid']:
    # Move to quarantine
    os.remove(file_path)
    raise SecurityError(result['error'])
```

**2. MIME Validation:**
- File content is analyzed (not just extension)
- Detects spoofed extensions (e.g., .exe renamed to .pdf)
- Rejects mismatched file types

**3. Virus Scanning:**
- Each file scanned with ClamAV
- Infected files rejected immediately
- Clean files logged and allowed

---

## 🔧 Production Configuration

### Secure File Storage

**Current (Development):**
```
uploads/
  ├── file1.pdf
  └── file2.docx
```

**Production (Recommended):**
```
/var/uploads/tdis/          ← Outside web root
  ├── file1.pdf
  └── file2.docx

/var/www/tdis/app/          ← Application root
  ├── app.py
  ├── routes.py
  └── ...
```

**Update .env for production:**
```env
UPLOAD_FOLDER=/var/uploads/tdis/
QUARANTINE_FOLDER=/var/uploads/tdis_quarantine/
```

**Set proper permissions:**
```bash
# Create directories
sudo mkdir -p /var/uploads/tdis
sudo mkdir -p /var/uploads/tdis_quarantine

# Set ownership
sudo chown www-data:www-data /var/uploads/tdis
sudo chown www-data:www-data /var/uploads/tdis_quarantine

# Set permissions (write for app, no public access)
sudo chmod 750 /var/uploads/tdis
sudo chmod 750 /var/uploads/tdis_quarantine
```

### ClamAV Performance Tuning

For production, optimize ClamAV configuration:

**Edit `/etc/clamav/clamd.conf`:**
```conf
# Increase timeout for large files
ReadTimeout 300

# Increase max file size
MaxFileSize 500M
MaxScanSize 500M

# Enable multi-threading
MaxThreads 4

# Optimize scanning
ScanPDF yes
ScanOLE2 yes
ScanHTML yes
```

**Restart daemon:**
```bash
sudo systemctl restart clamav-daemon
```

---

## 📊 Monitoring and Logging

### View Security Logs

```bash
# Application logs
tail -f logs/app.log | grep -i "security\|virus\|mime"

# ClamAV logs (Linux)
sudo tail -f /var/log/clamav/clamav.log
```

### Key Log Messages

**Successful Validation:**
```
INFO - File document.pdf passed MIME validation: application/pdf
INFO - File document.pdf is clean (no viruses)
INFO - File document.pdf passed all security validations
```

**Virus Detected:**
```
ERROR - 🦠 VIRUS DETECTED in uploads/infected.pdf: Win.Test.EICAR_HDB-1
ERROR - 🦠 Rejecting infected file infected.pdf: Win.Test.EICAR_HDB-1
```

**MIME Type Mismatch:**
```
WARNING - File extension mismatch for fake.pdf: extension=.pdf, mime=application/x-msdownload
WARNING - Rejected file fake.pdf with MIME type: application/x-msdownload
```

---

## 🧪 Testing with EICAR Test File

Test virus scanning with the EICAR test file (harmless test virus):

```bash
# Download EICAR test file
curl -o eicar.pdf https://www.eicar.org/download/eicar.com.txt

# Try to upload via API
curl -X POST -F "file=@eicar.pdf" http://localhost:5000/api/upload

# Expected response:
# {"error": "Virus detected: Win.Test.EICAR_HDB-1", "status": "error"}
```

**Note:** The EICAR file is a standard test file recognized by all antivirus software. It is NOT malicious.

---

## ⚠️ Troubleshooting

### Issue: "ClamAV not available"

**Symptoms:**
```
❌ ClamAV not available
Warning: Virus scanning not available
```

**Solutions:**

1. **Check if ClamAV is running:**
   ```bash
   # Windows
   tasklist | findstr clamd
   
   # Linux
   sudo systemctl status clamav-daemon
   
   # macOS
   brew services list | grep clamav
   ```

2. **Start ClamAV:**
   ```bash
   # Windows
   clamd
   
   # Linux
   sudo systemctl start clamav-daemon
   
   # macOS
   brew services start clamav
   ```

3. **Check socket connection:**
   ```bash
   # Test connection
   python -c "import clamd; cd = clamd.ClamdUnixSocket(); print(cd.ping())"
   ```

### Issue: "python-magic not found"

**Symptoms:**
```
ImportError: No module named 'magic'
```

**Solution:**
```bash
pip install python-magic python-magic-bin
```

### Issue: "File validation failed"

**Check:**
1. File is in allowed MIME types
2. Extension matches content
3. File is not corrupted
4. File size is under limit

**Debug:**
```python
python file_security.py  # Run diagnostic
```

### Issue: Slow upload processing

**Causes:**
- Large files (100MB+)
- ClamAV scanning takes time
- Network/disk I/O

**Solutions:**
1. Increase timeout in frontend
2. Implement async processing (Celery)
3. Show progress indicator to user

---

## 📋 Security Checklist

### Installation
- [ ] Python packages installed
- [ ] ClamAV installed
- [ ] ClamAV daemon running
- [ ] Virus definitions updated

### Configuration
- [ ] `.env` updated with security settings
- [ ] MIME validation enabled
- [ ] Virus scanning enabled (when ClamAV ready)
- [ ] Upload folder configured
- [ ] Quarantine folder created

### Testing
- [ ] Diagnostic test passed
- [ ] Test file upload successful
- [ ] MIME validation working
- [ ] Virus scan working
- [ ] EICAR test file rejected

### Production
- [ ] Files stored outside web root
- [ ] Proper permissions set
- [ ] ClamAV optimized for performance
- [ ] Monitoring and logging configured
- [ ] Quarantine process documented

---

## 🔄 Maintenance

### Daily
- Monitor security logs for suspicious activity
- Check quarantine folder for flagged files

### Weekly
- Update ClamAV virus definitions
  ```bash
  freshclam
  ```

### Monthly
- Review quarantined files
- Update python-magic database
- Test virus scanning with EICAR

### Quarterly
- Review and update MIME type whitelist
- Security audit of file handling
- Performance optimization review

---

## 📞 Support

**ClamAV Documentation:** https://docs.clamav.net/  
**python-magic:** https://github.com/ahupp/python-magic  
**Security Issues:** Review `SECURITY_SETUP.md`

---

**Last Updated:** December 29, 2026  
**Tested On:** Windows 11, Python 3.11  
**ClamAV Version:** 1.0+
