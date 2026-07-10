#!/bin/bash
# Development environment setup script for Tender Document Extraction API

set -e

echo "=========================================="
echo "Tender API - Development Setup"
echo "=========================================="
echo ""

# Check if Python 3.9+ is installed
echo "[1/7] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version found"

# Create virtual environment
echo ""
echo "[2/7] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "✓ Virtual environment already exists"
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "[3/7] Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo ""
echo "[4/7] Installing dependencies..."
pip install --upgrade pip setuptools wheel > /dev/null
pip install -r requirements.txt > /dev/null
echo "✓ Dependencies installed"

# Install dev dependencies
echo ""
echo "[5/7] Installing development dependencies..."
pip install -r requirements-dev.txt > /dev/null
echo "✓ Development dependencies installed"

# Create uploads directory
echo ""
echo "[6/7] Creating uploads directory..."
mkdir -p uploads
echo "✓ Uploads directory created"

# Initialize database
echo ""
echo "[7/7] Initializing database..."
python3 << 'EOF'
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
    print("✓ Database initialized")
EOF

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the development server, run:"
echo ""
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Or use the manage script:"
echo ""
echo "  python manage.py run --debug"
echo ""
echo "The API will be available at: http://localhost:5000"
echo "API Documentation: http://localhost:5000/"
echo ""
