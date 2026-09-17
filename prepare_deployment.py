#!/usr/bin/env python3
"""
Deployment Preparation Script for PythonAnywhere

This script prepares your TDIS app for PythonAnywhere deployment by:
1. Creating a deployment package
2. Checking for common issues
3. Generating deployment instructions
"""

import os
import sys
import json
import shutil
from pathlib import Path

def check_requirements():
    """Check if all required files exist"""
    print("🔍 Checking required files...")
    
    required_files = [
        'app.py',
        'config.py',
        'models.py',
        'routes.py',
        'requirements.txt',
        '.env.pythonanywhere.template',
        'wsgi_pythonanywhere.py',
        'DEPLOYMENT_PYTHONANYWHERE.md'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
            print(f"  ❌ Missing: {file}")
        else:
            print(f"  ✅ Found: {file}")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required files")
        return False
    
    print("\n✅ All required files present")
    return True

def check_dependencies():
    """Check requirements.txt for PythonAnywhere compatibility"""
    print("\n🔍 Checking dependencies...")
    
    with open('requirements.txt', 'r') as f:
        reqs = f.read()
    
    # Check for psycopg2-binary (PostgreSQL driver)
    if 'psycopg2-binary' in reqs:
        print("  ✅ PostgreSQL driver found (requires paid PythonAnywhere account)")
    
    # Check for Flask and essential packages
    essential = ['Flask', 'Flask-SQLAlchemy', 'Flask-Migrate', 'Flask-CORS', 'gunicorn']
    for pkg in essential:
        if pkg in reqs:
            print(f"  ✅ {pkg} found")
        else:
            print(f"  ⚠️  {pkg} not found")
    
    return True

def check_migrations():
    """Check if migrations are set up"""
    print("\n🔍 Checking database migrations...")
    
    migrations_dir = Path('migrations')
    if migrations_dir.exists():
        versions = list((migrations_dir / 'versions').glob('*.py'))
        print(f"  ✅ Migrations directory exists with {len(versions)} migration(s)")
        return True
    else:
        print("  ❌ Migrations directory not found")
        print("     Run: flask db init && flask db migrate -m 'initial'")
        return False

def create_deployment_package():
    """Create a deployment-ready package"""
    print("\n📦 Creating deployment package...")
    
    # Files and directories to exclude
    exclude = [
        '__pycache__',
        '.git',
        '.venv',
        'venv',
        'node_modules',
        'instance',
        'uploads',
        'logs',
        '.pytest_cache',
        '*.pyc',
        '*.pyo',
        '.env',
        '.DS_Store',
        'frontend/node_modules',
        'frontend/build'
    ]
    
    deployment_dir = Path('deployment_package')
    if deployment_dir.exists():
        shutil.rmtree(deployment_dir)
    
    deployment_dir.mkdir()
    
    print(f"  📁 Created: {deployment_dir}")
    print("  ℹ️  Manual upload or git push recommended instead")
    
    return True

def generate_checklist():
    """Generate a deployment checklist"""
    print("\n📋 Deployment Checklist:")
    
    checklist = [
        "Create PythonAnywhere account (paid for PostgreSQL)",
        "Create PostgreSQL database in Databases tab",
        "Upload code via git or file upload",
        "Create virtual environment: python3.11 -m venv venv",
        "Install dependencies: pip install -r requirements.txt",
        "Copy .env.pythonanywhere.template to .env and update values",
        "Run migrations: flask db upgrade",
        "Create uploads/ and logs/ directories",
        "Configure WSGI file in Web tab",
        "Set environment variables in Web tab",
        "Build React frontend locally: npm run build",
        "Upload frontend/build/ to PythonAnywhere",
        "Configure static files mappings",
        "Reload web app",
        "Test endpoints: /api/health, /api/users",
    ]
    
    for i, item in enumerate(checklist, 1):
        print(f"  {i:2d}. [ ] {item}")
    
    return True

def show_next_steps():
    """Show next steps"""
    print("\n" + "="*70)
    print("🚀 NEXT STEPS FOR PYTHONANYWHERE DEPLOYMENT")
    print("="*70)
    
    print("""
1. Read the deployment guide:
   → Open: DEPLOYMENT_PYTHONANYWHERE.md
   
2. If using git (recommended):
   git init
   git add .
   git commit -m "Prepare for PythonAnywhere deployment"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   
3. On PythonAnywhere:
   - Open Bash console
   - git clone YOUR_GITHUB_REPO_URL
   - Follow steps in DEPLOYMENT_PYTHONANYWHERE.md
   
4. Key files for PythonAnywhere:
   ✓ wsgi_pythonanywhere.py → Use in WSGI configuration
   ✓ .env.pythonanywhere.template → Copy to .env and customize
   ✓ requirements.txt → Install in venv
   
5. Important URLs (after deployment):
   - Your app: https://YOUR_USERNAME.pythonanywhere.com
   - Backend API: https://YOUR_USERNAME.pythonanywhere.com/api/health
   - Logs: Web tab → Log files section
""")
    
    print("="*70)

def main():
    """Main preparation flow"""
    print("="*70)
    print("🚀 TDIS PythonAnywhere Deployment Preparation")
    print("="*70)
    
    os.chdir(Path(__file__).parent)
    
    all_good = True
    
    if not check_requirements():
        all_good = False
    
    if not check_dependencies():
        all_good = False
    
    if not check_migrations():
        all_good = False
    
    if all_good:
        print("\n" + "="*70)
        print("✅ PRE-DEPLOYMENT CHECKS PASSED")
        print("="*70)
        
        generate_checklist()
        show_next_steps()
        
        return 0
    else:
        print("\n" + "="*70)
        print("❌ PRE-DEPLOYMENT CHECKS FAILED")
        print("="*70)
        print("Fix the issues above before deploying.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
