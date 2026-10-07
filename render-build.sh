#!/usr/bin/env bash
# Render build script for TDIS backend

set -e  # Exit on error

echo "===================================="
echo "Starting TDIS Backend Build"
echo "===================================="

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p /var/data/uploads
mkdir -p /var/data/logs
mkdir -p /var/data/quarantine
mkdir -p instance

# Download NLTK data (required for text extraction)
echo "📚 Downloading NLTK data..."
python -c "
import nltk
import ssl

# Handle SSL certificate issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)
print('✅ NLTK data downloaded successfully')
"

# Initialize database schema
echo "🗄️ Initializing database..."
python -c "
from app import create_app
from models import db

app = create_app('production')
with app.app_context():
    db.create_all()
    print('✅ Database tables created')
"

echo "===================================="
echo "✅ Build Complete!"
echo "===================================="
