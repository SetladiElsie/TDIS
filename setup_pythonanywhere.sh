#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# PythonAnywhere Setup Script
# ══════════════════════════════════════════════════════════════════════════════
# Run this script in a PythonAnywhere Bash console after uploading/cloning code
#
# Usage:
#   bash setup_pythonanywhere.sh
#

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════════════════"
echo "🚀 TDIS PythonAnywhere Setup"
echo "════════════════════════════════════════════════════════════════════════════"

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_DIR="$HOME/tdis"
PYTHON_VERSION="python3.11"

# ── Step 1: Navigate to project ──────────────────────────────────────────────
echo ""
echo "📁 Step 1: Navigating to project directory..."
cd "$PROJECT_DIR" || {
    echo "❌ Error: Project directory $PROJECT_DIR not found"
    echo "   Please upload or clone your code first"
    exit 1
}
echo "✅ Current directory: $(pwd)"

# ── Step 2: Create virtual environment ───────────────────────────────────────
echo ""
echo "🐍 Step 2: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  venv already exists, skipping creation"
else
    $PYTHON_VERSION -m venv venv
    echo "✅ Virtual environment created"
fi

# ── Step 3: Activate and upgrade pip ─────────────────────────────────────────
echo ""
echo "📦 Step 3: Activating venv and upgrading pip..."
source venv/bin/activate
pip install --upgrade pip
echo "✅ pip upgraded"

# ── Step 4: Install dependencies ─────────────────────────────────────────────
echo ""
echo "📚 Step 4: Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# ── Step 5: Check environment file ───────────────────────────────────────────
echo ""
echo "🔧 Step 5: Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.pythonanywhere.template" ]; then
        echo "⚠️  No .env file found. Copying from template..."
        cp .env.pythonanywhere.template .env
        echo "✅ .env created from template"
        echo "⚠️  IMPORTANT: Edit .env and update all YOUR_* placeholders!"
    else
        echo "❌ Error: No .env file and no template found"
        exit 1
    fi
else
    echo "✅ .env file exists"
fi

# ── Step 6: Create required directories ──────────────────────────────────────
echo ""
echo "📂 Step 6: Creating required directories..."
mkdir -p uploads logs instance
chmod 755 uploads logs instance
echo "✅ Directories created: uploads/, logs/, instance/"

# ── Step 7: Check database configuration ─────────────────────────────────────
echo ""
echo "🗄️  Step 7: Checking database configuration..."
if grep -q "postgresql://" .env 2>/dev/null; then
    echo "✅ PostgreSQL configured"
    echo "   Make sure you've created the database in PythonAnywhere Databases tab"
elif grep -q "sqlite://" .env 2>/dev/null; then
    echo "✅ SQLite configured"
else
    echo "⚠️  No database URL found in .env"
    echo "   Please set DATABASE_URL in .env"
fi

# ── Step 8: Run database migrations ──────────────────────────────────────────
echo ""
echo "🔄 Step 8: Running database migrations..."
export FLASK_APP=app.py
if [ -d "migrations" ]; then
    flask db upgrade
    echo "✅ Migrations applied"
else
    echo "⚠️  No migrations directory found"
    echo "   Run: flask db init && flask db migrate -m 'initial'"
fi

# ── Step 9: Verify installation ──────────────────────────────────────────────
echo ""
echo "✅ Step 9: Verifying installation..."
python -c "from app import create_app; app = create_app(); print('✅ App imports successfully')"

# ── Final instructions ────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Edit .env file and update all YOUR_* placeholders:"
echo "   nano .env"
echo ""
echo "2. Configure WSGI in PythonAnywhere Web tab:"
echo "   - Copy content from wsgi_pythonanywhere.py"
echo "   - Update YOUR_USERNAME to your actual username"
echo ""
echo "3. Set environment variables in Web tab (optional if using .env)"
echo ""
echo "4. Configure static files for React frontend:"
echo "   URL: /"
echo "   Directory: $PROJECT_DIR/frontend/build"
echo ""
echo "5. Reload your web app"
echo ""
echo "6. Test endpoints:"
echo "   https://YOUR_USERNAME.pythonanywhere.com/api/health"
echo "   https://YOUR_USERNAME.pythonanywhere.com/api/users"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
