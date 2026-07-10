"""Webhook handling for event notifications"""

import requests
import json
from datetime import datetime
from logger import get_logger
from errors import WebhookError

logger = get_logger(__name__)


class WebhookHandler:
    """Send and manage webhooks"""
    
    # Event types
    EVENTS = {
        'extraction.completed': 'Extraction completed successfully',
        'extraction.failed': 'Extraction failed',
        'upload.completed': 'File upload completed',
        'batch.completed': 'Batch processing completed',
    }
    
    def __init__(self, timeout=30, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries
    
    def send_webhook(self, webhook_url, event_type, payload, webhook_secret=None):
        """Send webhook to external service"""
        try:
            # Build payload
            webhook_payload = {
                'event': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': payload
            }
            
            # Add signature if secret provided
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Event': event_type,
            }
            
            if webhook_secret:
                import hmac
                import hashlib
                
                signature = hmac.new(
                    webhook_secret.encode(),
                    json.dumps(webhook_payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                
                headers['X-Webhook-Signature'] = signature
            
            # Send POST request
            response = requests.post(
                webhook_url,
                json=webhook_payload,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            logger.info(f"Webhook sent successfully: {event_type} to {webhook_url}")
            
            return {
                'status': 'sent',
                'event': event_type,
                'url': webhook_url,
                'response_code': response.status_code
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook send failed: {str(e)}")
            raise WebhookError(f'Webhook delivery failed: {str(e)}')
    
    def send_webhook_async(self, webhook_id, event_type, payload):
        """Queue webhook for async sending (via Celery)"""
        try:
            from celery_app import celery_app
            
            task = celery_app.send_task(
                'send_webhook_task',
                args=[webhook_id, event_type, payload]
            )
            
            logger.debug(f"Webhook queued for async sending: task_id={task.id}")
            return {'task_id': task.id, 'status': 'queued'}
        
        except Exception as e:
            logger.error(f"Failed to queue webhook: {str(e)}")
            raise WebhookError(f'Failed to queue webhook: {str(e)}')
    
    def build_extraction_payload(self, extraction):
        """Build payload for extraction event"""
        return {
            'extraction_id': extraction.id,
            'upload_id': extraction.upload_id,
            'status': extraction.status,
            'extracted_data': {
                'tender_id': extraction.tender_id,
                'tender_name': extraction.tender_name,
                'organization': extraction.organization,
                'closing_date': extraction.closing_date.isoformat() if extraction.closing_date else None,
                'budget': {
                    'amount': extraction.budget_amount,
                    'currency': extraction.budget_currency
                },
                'location': extraction.location,
            },
            'confidence_scores': extraction.confidence_scores or {},
            'processing_time_ms': extraction.processing_time_ms,
            'error_message': extraction.error_message
        }
    
    def build_upload_payload(self, upload):
        """Build payload for upload event"""
        return {
            'upload_id': upload.id,
            'filename': upload.filename,
            'file_size': upload.file_size,
            'file_type': upload.file_type,
            'status': upload.status,
            'upload_timestamp': upload.upload_timestamp.isoformat()
        }
    
    def build_batch_payload(self, batch_job):
        """Build payload for batch job event"""
        return {
            'job_id': batch_job.id,
            'name': batch_job.name,
            'status': batch_job.status,
            'progress': {
                'total': batch_job.total_files,
                'processed': batch_job.processed_files,
                'failed': batch_job.failed_files
            },
            'completed_at': batch_job.completed_at.isoformat() if batch_job.completed_at else None
        }


class WebhookEventQueue:
    """Queue and manage webhook events"""
    
    def __init__(self):
        self.handler = WebhookHandler()
    
    def queue_event(self, db, user_id, event_type, webhooks, payload):
        """Queue events for registered webhooks"""
        from models import WebhookEvent
        
        queued_events = []
        
        for webhook in webhooks:
            if event_type not in webhook.events:
                continue
            
            event = WebhookEvent(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=payload,
                status='pending'
            )
            
            db.session.add(event)
            queued_events.append(event)
        
        try:
            db.session.commit()
            logger.info(f"Queued {len(queued_events)} webhook events")
            return queued_events
        except Exception as e:
            logger.error(f"Failed to queue webhook events: {str(e)}")
            db.session.rollback()
            return []
    
    def process_pending_events(self, db):
        """Process pending webhook events"""
        from models import WebhookEvent
        
        pending = db.session.query(WebhookEvent).filter_by(status='pending').all()
        
        processed = 0
        for event in pending:
            try:
                self.handler.send_webhook(
                    event.webhook.url,
                    event.event_type,
                    event.payload
                )
                
                event.status = 'sent'
                event.sent_at = datetime.utcnow()
                processed += 1
            
            except Exception as e:
                event.attempts += 1
                event.error_message = str(e)
                
                if event.attempts >= self.handler.max_retries:
                    event.status = 'failed'
                    logger.error(f"Webhook event failed after {event.attempts} attempts: {str(e)}")
                else:
                    event.status = 'retrying'
                    logger.warning(f"Webhook event retry {event.attempts}: {str(e)}")
        
        try:
            db.session.commit()
            logger.info(f"Processed {processed} webhook events")
            return {'processed': processed}
        except Exception as e:
            logger.error(f"Failed to save webhook events: {str(e)}")
            db.session.rollback()
            return {'error': str(e)}


# Global handlers
webhook_handler = WebhookHandler()
webhook_queue = WebhookEventQueue()
