#!/usr/bin/env python
"""
Management script for the Tender Document Extraction API
"""

import os
import sys
from app import create_app, db
from models import Upload, Extraction
import click

app = create_app()

@click.group()
def cli():
    """Management commands"""
    pass

@cli.command()
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

@cli.command()
def drop_db():
    """Drop all database tables (WARNING: destructive)"""
    if click.confirm('Are you sure you want to drop all tables? This cannot be undone!'):
        with app.app_context():
            db.drop_all()
            print("All tables dropped!")
    else:
        print("Operation cancelled.")

@cli.command()
def reset_db():
    """Reset database (drop and reinitialize)"""
    if click.confirm('Are you sure you want to reset the database? All data will be lost!'):
        with app.app_context():
            db.drop_all()
            db.create_all()
            print("Database reset successfully!")
    else:
        print("Operation cancelled.")

@cli.command()
def create_uploads_dir():
    """Create uploads directory"""
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads/')
    os.makedirs(upload_folder, exist_ok=True)
    print(f"Uploads directory created at: {upload_folder}")

@cli.command()
def cleanup_uploads():
    """Clean up old uploaded files"""
    from datetime import datetime, timedelta
    
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads/')
    retention_days = 30
    cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
    
    with app.app_context():
        old_uploads = Upload.query.filter(Upload.upload_timestamp < cutoff_time).all()
        
        count = 0
        for upload in old_uploads:
            # Delete file
            if os.path.exists(upload.upload_path):
                try:
                    os.remove(upload.upload_path)
                    count += 1
                except Exception as e:
                    print(f"Error deleting {upload.upload_path}: {e}")
            
            # Delete record
            db.session.delete(upload)
        
        db.session.commit()
        print(f"Cleaned up {count} old uploaded files (older than {retention_days} days)")

@cli.command()
def show_stats():
    """Show database statistics"""
    with app.app_context():
        total_uploads = Upload.query.count()
        total_extractions = Extraction.query.count()
        completed_extractions = Extraction.query.filter_by(status='completed').count()
        failed_extractions = Extraction.query.filter_by(status='failed').count()
        processing_extractions = Extraction.query.filter_by(status='processing').count()
        
        print("\n=== Database Statistics ===")
        print(f"Total Uploads: {total_uploads}")
        print(f"Total Extractions: {total_extractions}")
        print(f"  - Completed: {completed_extractions}")
        print(f"  - Processing: {processing_extractions}")
        print(f"  - Failed: {failed_extractions}")
        print("\n")

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to run on')
@click.option('--port', default=5000, type=int, help='Port to run on')
@click.option('--debug', is_flag=True, help='Run in debug mode')
def run(host, port, debug):
    """Run the development server"""
    # Create uploads directory
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads/')
    os.makedirs(upload_folder, exist_ok=True)
    
    print(f"Starting server on {host}:{port}...")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    cli()
