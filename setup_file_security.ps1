# ================================================================
# TDIS File Security Setup Script (PowerShell)
# ================================================================
# This script installs and configures file security features:
# - python-magic for MIME type validation
# - ClamAV for virus scanning
# - Creates necessary directories
# - Tests the installation
# ================================================================

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "    TDIS File Security Setup" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (!$isAdmin) {
    Write-Host "⚠️  Warning: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "   Some features may require elevated privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Check if virtual environment is activated
if (!$env:VIRTUAL_ENV) {
    Write-Host "❌ Virtual environment not activated!" -ForegroundColor Red
    Write-Host "   Please activate with: .\.venv\Scripts\activate" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------
# Step 1: Install Python Packages
# ----------------------------------------------------------------
Write-Host "Step 1: Installing Python packages..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor DarkGray

pip install python-magic python-magic-bin clamd
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install Python packages" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python packages installed" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------
# Step 2: Check for ClamAV
# ----------------------------------------------------------------
Write-Host "Step 2: Checking for ClamAV..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor DarkGray

$clamavInstalled = $false
$clamdPath = Get-Command clamd -ErrorAction SilentlyContinue

if ($clamdPath) {
    Write-Host "✅ ClamAV found at: $($clamdPath.Source)" -ForegroundColor Green
    $clamavInstalled = $true
} else {
    Write-Host "❌ ClamAV not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installation Options:" -ForegroundColor Yellow
    Write-Host "  Option 1 (Recommended): Using Chocolatey" -ForegroundColor White
    Write-Host "    choco install clamav" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Option 2: Manual Download" -ForegroundColor White
    Write-Host "    Visit: https://www.clamav.net/downloads" -ForegroundColor DarkGray
    Write-Host ""
    
    $install = Read-Host "Would you like to install ClamAV with Chocolatey? (y/n)"
    if ($install -eq 'y' -or $install -eq 'Y') {
        # Check if Chocolatey is installed
        $chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue
        if (!$chocoInstalled) {
            Write-Host "❌ Chocolatey not installed" -ForegroundColor Red
            Write-Host "   Install from: https://chocolatey.org/install" -ForegroundColor Yellow
        } else {
            Write-Host "Installing ClamAV..." -ForegroundColor Yellow
            choco install clamav -y
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ ClamAV installed" -ForegroundColor Green
                $clamavInstalled = $true
            }
        }
    }
}

Write-Host ""

# ----------------------------------------------------------------
# Step 3: Update Virus Definitions
# ----------------------------------------------------------------
if ($clamavInstalled) {
    Write-Host "Step 3: Updating virus definitions..." -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host "This may take 5-15 minutes on first run..." -ForegroundColor Yellow
    
    freshclam
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Virus definitions updated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Failed to update virus definitions" -ForegroundColor Yellow
        Write-Host "   Run 'freshclam' manually later" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# ----------------------------------------------------------------
# Step 4: Create Directories
# ----------------------------------------------------------------
Write-Host "Step 4: Creating directories..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor DarkGray

$directories = @("uploads", "quarantine", "logs")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓  Exists: $dir" -ForegroundColor DarkGray
    }
}

Write-Host ""

# ----------------------------------------------------------------
# Step 5: Update .env File
# ----------------------------------------------------------------
Write-Host "Step 5: Updating .env configuration..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor DarkGray

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    # Check if security settings exist
    if ($envContent -notmatch "ENABLE_FILE_MIME_VALIDATION") {
        # Add security settings
        Add-Content ".env" "`n# ── File Security ─────────────────────────────────────────────────────────────"
        Add-Content ".env" "ENABLE_FILE_MIME_VALIDATION=True"
        
        if ($clamavInstalled) {
            Add-Content ".env" "ENABLE_VIRUS_SCANNING=True"
        } else {
            Add-Content ".env" "ENABLE_VIRUS_SCANNING=False"
        }
        
        Add-Content ".env" "QUARANTINE_FOLDER=quarantine/"
        
        Write-Host "✅ Added security settings to .env" -ForegroundColor Green
    } else {
        Write-Host "✓  Security settings already in .env" -ForegroundColor DarkGray
    }
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "   Copy .env.example to .env" -ForegroundColor Yellow
}

Write-Host ""

# ----------------------------------------------------------------
# Step 6: Start ClamAV (if installed)
# ----------------------------------------------------------------
if ($clamavInstalled) {
    Write-Host "Step 6: Starting ClamAV daemon..." -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    
    # Check if clamd is already running
    $clamdRunning = Get-Process -Name clamd -ErrorAction SilentlyContinue
    
    if ($clamdRunning) {
        Write-Host "✅ ClamAV daemon already running" -ForegroundColor Green
    } else {
        Write-Host "Starting ClamAV daemon..." -ForegroundColor Yellow
        Start-Process clamd -WindowStyle Hidden
        Start-Sleep -Seconds 2
        
        $clamdRunning = Get-Process -Name clamd -ErrorAction SilentlyContinue
        if ($clamdRunning) {
            Write-Host "✅ ClamAV daemon started" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Could not start ClamAV daemon" -ForegroundColor Yellow
            Write-Host "   Try running 'clamd' manually" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
}

# ----------------------------------------------------------------
# Step 7: Run Diagnostic Test
# ----------------------------------------------------------------
Write-Host "Step 7: Running diagnostic test..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

python file_security.py

Write-Host ""

# ----------------------------------------------------------------
# Summary
# ----------------------------------------------------------------
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "    Setup Complete!" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Status Summary:" -ForegroundColor Yellow
Write-Host "  Python Packages: ✅ Installed" -ForegroundColor Green
Write-Host "  ClamAV: $(if ($clamavInstalled) { '✅ Installed' } else { '❌ Not Installed' })" -ForegroundColor $(if ($clamavInstalled) { 'Green' } else { 'Red' })
Write-Host "  Directories: ✅ Created" -ForegroundColor Green
Write-Host "  Configuration: ✅ Updated" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review FILE_SECURITY_SETUP.md for details" -ForegroundColor White
Write-Host "  2. $(if (!$clamavInstalled) { 'Install ClamAV (optional)' } else { 'Test file upload with virus scanning' })" -ForegroundColor White
Write-Host "  3. Restart Flask application" -ForegroundColor White
Write-Host ""

Write-Host "Test the features:" -ForegroundColor Yellow
Write-Host "  python file_security.py" -ForegroundColor DarkGray
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  FILE_SECURITY_SETUP.md" -ForegroundColor DarkGray
Write-Host ""
