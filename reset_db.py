"""Reset database - clear all stale extraction records."""
from app import create_app
from models import db, Extraction, Upload

app = create_app()
with app.app_context():
    n_e = Extraction.query.delete()
    n_u = Upload.query.delete()
    db.session.commit()
    print(f"Cleared {n_e} extraction(s) and {n_u} upload(s).")
    print("Database is clean. Upload documents fresh from the UI.")
