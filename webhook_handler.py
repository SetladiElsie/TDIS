"""Webhook handling for event notifications"""

import requests
import json
from datetime import datetime
from logger import get_logger
from errors import WebhookError

logger = get_logger(__name__)


class WebhookHandler:
    """Send webhooks to external services"""

    EVENTS = {
        'extraction.completed': 'Extraction completed successfully',
        'extraction.failed': 'Extraction failed',
        'upload.completed': 'File upload completed',
    }

    def __init__(self, timeout=30, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries

    def send_webhook(self, webhook_url, event_type, payload, webhook_secret=None):
        """Send webhook to external service"""
        try:
            webhook_payload = {
                'event': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': payload
            }

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


# Global handler instance
webhook_handler = WebhookHandler()
