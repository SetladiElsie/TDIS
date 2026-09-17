"""
WSGI Configuration for PythonAnywhere Deployment

Instructions:
1. Upload this file to /home/YOUR_USERNAME/tdis/
2. In PythonAnywhere Web tab, edit WSGI configuration file
3. Replace entire content with this file's content
4. Update YOUR_USERNAME to your actual PythonAnywhere username
"""

import sys
import os

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_HOME = '/home/YOUR_USERNAME/tdis'  # ← CHANGE THIS to your username
VENV_PYTHON = os.path.join(PROJECT_HOME, 'venv/bin/python')

# ── Add project to Python path ────────────────────────────────────────────────
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

# ── Activate virtual environment ──────────────────────────────────────────────
activate_this = os.path.join(PROJECT_HOME, 'venv/bin/activate_this.py')
try:
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))
except FileNotFoundError:
    # Fallback: manually set venv paths
    import site
    venv_site_packages = os.path.join(PROJECT_HOME, 'venv/lib/python3.11/site-packages')
    site.addsitedir(venv_site_packages)

# ── Load environment variables from .env ──────────────────────────────────────
from dotenv import load_dotenv
env_path = os.path.join(PROJECT_HOME, '.env')
load_dotenv(env_path)

# ── Import and configure Flask app ────────────────────────────────────────────
from app import create_app

# Use 'production' config
application = create_app('production')

# ── Logging for debugging ─────────────────────────────────────────────────────
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("WSGI application loaded successfully")
logger.info(f"Python path: {sys.path}")
logger.info(f"Environment: {application.config.get('ENV', 'unknown')}")
logger.info(f"Database URI: {application.config.get('SQLALCHEMY_DATABASE_URI', 'not set')[:50]}...")
