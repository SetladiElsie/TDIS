"""Celery configuration for async tasks"""

from celery import Celery
from celery.schedules import crontab
import os
from logger import get_logger

logger = get_logger(__name__)


def make_celery(app=None):
    """Create Celery instance"""
    celery_app = Celery(
        app.import_name if app else __name__,
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30*60,  # 30 minutes hard limit
        task_soft_time_limit=25*60,  # 25 minutes soft limit
        result_expires=3600,  # Results expire after 1 hour
        broker_connection_retry_on_startup=True,
    )
    
    if app:
        celery_app.conf.update(app.config)
        
        class ContextTask(celery_app.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery_app.Task = ContextTask
    
    return celery_app


# Create celery app instance
celery_app = Celery(
    'tender_extraction',
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30*60,
    task_soft_time_limit=25*60,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)

# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    'cleanup-old-uploads': {
        'task': 'celery_tasks.cleanup_old_uploads',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'generate-daily-report': {
        'task': 'celery_tasks.generate_daily_report',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    'backup-database': {
        'task': 'celery_tasks.backup_database',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'process-webhooks': {
        'task': 'celery_tasks.process_pending_webhooks',
        'schedule': 60,  # Every minute
    },
}


# Task definitions
@celery_app.task(bind=True, name='extract_document')
def extract_document_async(self, upload_id, extraction_id):
    """Async document extraction task"""
    try:
        from models import db, Extraction, Upload
        
        # Update extraction status
        extraction = db.session.query(Extraction).filter_by(id=extraction_id).first()
        if not extraction:
            return {'error': 'Extraction not found'}
        
        extraction.status = 'processing'
        db.session.commit()
        
        # Update task state
        self.update_state(state='PROCESSING', meta={'status': 'Extracting document...'})
        
        # Import extraction function
        from extraction import process_extraction
        
        # Perform extraction
        result = process_extraction(upload_id)
        
        # Update extraction with results
        extraction.status = 'completed'
        extraction.scope_of_work = result.get('scope_of_work')
        extraction.closing_date = result.get('closing_date')
        extraction.tender_id = result.get('tender_id')
        extraction.tender_name = result.get('tender_name')
        extraction.organization = result.get('organization')
        extraction.budget_amount = result.get('budget_amount')
        extraction.budget_currency = result.get('budget_currency')
        extraction.contact_email = result.get('contact_email')
        extraction.contact_phone = result.get('contact_phone')
        extraction.location = result.get('location')
        extraction.document_type = result.get('document_type')
        extraction.estimated_duration = result.get('estimated_duration')
        extraction.submission_format = result.get('submission_format')
        extraction.key_requirements = result.get('key_requirements')
        extraction.evaluation_criteria = result.get('evaluation_criteria')
        extraction.deliverables = result.get('deliverables')
        extraction.compulsory_documents = result.get('compulsory_documents')
        extraction.confidence_scores = result.get('confidence_scores')
        extraction.processing_time_ms = result.get('processing_time_ms')
        extraction.completed_at = db.func.now()
        
        db.session.commit()
        
        logger.info(f"Extraction {extraction_id} completed successfully")
        return {'status': 'completed', 'extraction_id': extraction_id}
    
    except Exception as e:
        logger.error(f"Extraction task failed: {str(e)}", exc_info=True)
        extraction = db.session.query(Extraction).filter_by(id=extraction_id).first()
        if extraction:
            extraction.status = 'failed'
            extraction.error_message = str(e)
            db.session.commit()
        
        return {'status': 'failed', 'error': str(e)}


@celery_app.task(name='cleanup_old_uploads')
def cleanup_old_uploads():
    """Clean up old upload files"""
    try:
        from models import db, Upload
        from datetime import datetime, timedelta
        import os
        
        # Delete uploads older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_uploads = db.session.query(Upload).filter(
            Upload.upload_timestamp < cutoff_date
        ).all()
        
        deleted_count = 0
        for upload in old_uploads:
            try:
                if os.path.exists(upload.upload_path):
                    os.remove(upload.upload_path)
                db.session.delete(upload)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete upload {upload.id}: {str(e)}")
        
        db.session.commit()
        logger.info(f"Cleanup task: deleted {deleted_count} old uploads")
        return {'deleted': deleted_count}
    
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}", exc_info=True)
        return {'error': str(e)}


@celery_app.task(name='generate_daily_report')
def generate_daily_report():
    """Generate daily statistics report"""
    try:
        from models import db, Upload, Extraction
        from datetime import datetime, timedelta
        
        today = datetime.utcnow().date()
        
        # Statistics
        total_uploads = db.session.query(Upload).filter(
            db.func.date(Upload.upload_timestamp) == today
        ).count()
        
        total_extractions = db.session.query(Extraction).filter(
            db.func.date(Extraction.created_at) == today,
            Extraction.status == 'completed'
        ).count()
        
        failed_extractions = db.session.query(Extraction).filter(
            db.func.date(Extraction.created_at) == today,
            Extraction.status == 'failed'
        ).count()
        
        logger.info(f"Daily Report - Uploads: {total_uploads}, "
                   f"Successful Extractions: {total_extractions}, "
                   f"Failed: {failed_extractions}")
        
        return {
            'date': str(today),
            'uploads': total_uploads,
            'extractions': total_extractions,
            'failures': failed_extractions
        }
    
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        return {'error': str(e)}


@celery_app.task(name='backup_database')
def backup_database():
    """Backup database"""
    try:
        from backup_manager import BackupManager
        
        backup_mgr = BackupManager()
        result = backup_mgr.create_backup()
        
        logger.info(f"Database backup completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Backup task failed: {str(e)}", exc_info=True)
        return {'error': str(e)}


@celery_app.task(name='process_pending_webhooks')
def process_pending_webhooks():
    """Process pending webhooks"""
    try:
        from models import db, WebhookEvent
        
        pending = db.session.query(WebhookEvent).filter_by(status='pending').all()
        
        processed = 0
        for event in pending:
            try:
                # Send webhook
                from webhook_handler import send_webhook
                send_webhook(event)
                event.status = 'sent'
                processed += 1
            except Exception as e:
                event.attempts += 1
                if event.attempts >= 3:
                    event.status = 'failed'
                logger.warning(f"Webhook processing failed: {str(e)}")
        
        db.session.commit()
        logger.debug(f"Webhook processing: {processed} processed")
        return {'processed': processed}
    
    except Exception as e:
        logger.error(f"Webhook processing task failed: {str(e)}", exc_info=True)
        return {'error': str(e)}
