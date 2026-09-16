from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import os
import csv
import json
from io import BytesIO, StringIO
import time
from threading import Thread

from models import db, User, Upload, Extraction
from extraction import process_document
import smtplib
from email.message import EmailMessage

api = Blueprint('api', __name__, url_prefix='/api')


# ── helpers ────────────────────────────────────────────────────────────────────


def _send_assignment_email(user, extraction):
    """Send a polished assignment notification email when a tender is assigned."""
    if not user or not getattr(user, 'email', None):
        return False

    smtp_server = os.getenv('MAIL_SERVER')
    smtp_port = int(os.getenv('MAIL_PORT', '587'))
    smtp_username = os.getenv('MAIL_USERNAME')
    smtp_password = os.getenv('MAIL_PASSWORD')
    sender_address = os.getenv('MAIL_FROM') or os.getenv('MAIL_SENDER') or smtp_username or 'tdis-no-reply@tia-solutions.co.za'

    if not smtp_server or not smtp_username or not smtp_password:
        current_app.logger.warning(
            'Assignment email skipped: MAIL_SERVER, MAIL_USERNAME, and MAIL_PASSWORD must be configured. '
            'Set them in the environment or .env file before assigning a tender.'
        )
        return False

    tender_name = extraction.tender_name or 'Untitled tender'
    tender_id = extraction.tender_id or 'N/A'
    org_name = getattr(extraction, 'organization', None) or 'N/A'
    closing_date = getattr(extraction, 'closing_date_formatted', None) or 'Not specified'
    scope = getattr(extraction, 'scope_of_work', None) or 'Scope details are still being reviewed.'

    subject = f'New tender assignment: {tender_name}'
    body = (
        f"Dear {user.name},\n\n"
        f"You have been assigned to the following tender:\n\n"
        f"Tender Name: {tender_name}\n"
        f"Tender ID: {tender_id}\n"
        f"Organisation: {org_name}\n"
        f"Closing Date: {closing_date}\n\n"
        f"Scope of Work:\n{scope}\n\n"
        f"Please log in to the TDIS portal to review the tender and update the status where needed.\n\n"
        f"Regards,\nTDIS Team"
    )

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = sender_address
    message['To'] = user.email
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        return True
    except Exception:
        return False

def _allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def _parse_date(date_str: str):
    """Try to parse a date string into a datetime object. Returns None on failure."""
    if not date_str:
        return None
    formats = [
        '%d %B %Y', '%d %b %Y',
        '%B %d, %Y', '%b %d, %Y',
        '%Y-%m-%d', '%Y/%m/%d',
        '%d-%m-%Y', '%d/%m/%Y',
        '%d %B %Y', '%d-%B-%Y',
    ]
    clean = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return None


# ── upload ─────────────────────────────────────────────────────────────────────

@api.route('/upload', methods=['POST'])
def upload_file():
    """Upload a tender document and save it to disk."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'code': 'NO_FILE'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No file selected', 'code': 'NO_FILE_SELECTED'}), 400

        allowed_ext = current_app.config.get(
            'ALLOWED_EXTENSIONS', {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'csv'})
        if not _allowed_file(file.filename, allowed_ext):
            return jsonify({
                'error': 'File format not supported',
                'code': 'UNSUPPORTED_FORMAT',
                'details': f'Supported formats: {", ".join(sorted(allowed_ext))}'
            }), 415

        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/')
        os.makedirs(upload_folder, exist_ok=True)

        upload_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        upload_path = os.path.join(upload_folder, f'{upload_id}_{filename}')
        file.save(upload_path)
        file_size = os.path.getsize(upload_path)

        assigned_user_id = request.form.get('assigned_user_id')
        assigned_user_name = None
        if assigned_user_id:
            user = User.query.get(assigned_user_id)
            if user:
                assigned_user_name = user.name
            else:
                return jsonify({'error': 'Assigned user not found', 'code': 'USER_NOT_FOUND'}), 400

        record = Upload(
            id=upload_id,
            filename=filename,
            file_type=file.content_type or '',
            file_size=file_size,
            upload_path=upload_path,
            status='uploaded',
            assigned_user_id=assigned_user_id,
            assigned_user_name=assigned_user_name,
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            'upload_id': upload_id,
            'filename': filename,
            'file_type': file.content_type,
            'upload_timestamp': datetime.utcnow().isoformat(),
            'file_size': file_size,
            'status': 'uploaded',
        }), 200

    except Exception as e:
        return jsonify({'error': str(e), 'code': 'UPLOAD_ERROR'}), 500


# ── extract ────────────────────────────────────────────────────────────────────

@api.route('/extract', methods=['POST'])
def extract_information():
    """Trigger extraction for a previously uploaded document."""
    try:
        data = request.json or {}
        upload_id = data.get('upload_id')
        if not upload_id:
            return jsonify({'error': 'upload_id is required', 'code': 'MISSING_UPLOAD_ID'}), 400

        upload = Upload.query.get(upload_id)
        if not upload:
            return jsonify({'error': 'Upload not found', 'code': 'UPLOAD_NOT_FOUND'}), 404

        extraction_id = str(uuid.uuid4())
        extraction = Extraction(
            id=extraction_id,
            upload_id=upload_id,
            status='processing',
            assigned_user_id=upload.assigned_user_id,
            assigned_user_name=upload.assigned_user_name,
        )
        db.session.add(extraction)
        db.session.commit()

        # Run extraction in the background so the API responds immediately
        _start_extraction_thread(extraction_id, upload.upload_path)

        return jsonify({
            'extraction_id': extraction_id,
            'upload_id': upload_id,
            'status': 'processing',
            'created_at': datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        return jsonify({'error': str(e), 'code': 'EXTRACTION_ERROR'}), 500


def _start_extraction_thread(extraction_id: str, upload_path: str):
    """Start extraction work in a background thread so the request returns quickly."""
    app = current_app._get_current_object()

    def _worker():
        with app.app_context():
            _run_extraction(extraction_id, upload_path)

    thread = Thread(target=_worker, daemon=True)
    thread.start()
    return thread


def _run_extraction(extraction_id: str, upload_path: str):
    """
    Run the extraction pipeline and persist every field to the database.
    Uses process_document() — the single entry point of the new engine.
    """
    start = time.time()
    extraction = Extraction.query.get(extraction_id)
    if not extraction:
        return

    try:
        file_ext = upload_path.rsplit('.', 1)[-1].lower() if '.' in upload_path else 'txt'

        # ── single call to the extraction engine ──
        fields = process_document(upload_path, file_ext)

        # ── scalar fields ──
        extraction.tender_id         = fields.get('tender_id') or None
        extraction.tender_name       = fields.get('tender_name') or None
        extraction.organization      = fields.get('organization') or None
        extraction.scope_of_work     = fields.get('scope_of_work') or None
        extraction.budget_amount     = fields.get('budget_amount') or None
        extraction.budget_currency   = fields.get('budget_currency') or 'ZAR'
        extraction.contact_email     = fields.get('contact_email') or None
        extraction.contact_phone     = fields.get('contact_phone') or None
        extraction.location          = fields.get('location') or None
        extraction.estimated_duration = fields.get('estimated_duration') or None
        extraction.submission_format = fields.get('submission_format') or None
        extraction.document_type     = fields.get('document_type') or 'RFQ/RFP'

        # ── list fields — guarantee they are lists, never None ──
        extraction.evaluation_criteria  = fields.get('evaluation_criteria') or []
        extraction.deliverables         = fields.get('deliverables') or []
        extraction.compulsory_documents = fields.get('compulsory_documents') or []
        extraction.mandatory_criteria   = fields.get('mandatory_criteria') or []
        extraction.pricing_schedule     = fields.get('pricing_schedule') or []
        extraction.key_requirements     = fields.get('mandatory_criteria') or fields.get('key_requirements') or []

        # ── closing date — store both formatted string and parsed datetime ──
        closing_str = fields.get('closing_date')
        if closing_str:
            extraction.closing_date_formatted = closing_str
            extraction.closing_date = _parse_date(closing_str)
        else:
            extraction.closing_date_formatted = None
            extraction.closing_date = None

        # ── confidence scores (1.0 if found, 0.0 if not) ──
        extraction.confidence_scores = {
            'tender_id':    1.0 if extraction.tender_id else 0.0,
            'closing_date': 1.0 if extraction.closing_date else 0.0,
            'scope_of_work': 1.0 if extraction.scope_of_work else 0.0,
            'organization': 1.0 if extraction.organization else 0.0,
            'budget':       1.0 if extraction.budget_amount else 0.0,
        }

        extraction.status = 'completed'
        extraction.completed_at = datetime.utcnow()
        extraction.processing_time_ms = int((time.time() - start) * 1000)
        db.session.commit()

    except Exception as e:
        extraction.status = 'failed'
        extraction.error_message = str(e)[:500]
        extraction.completed_at = datetime.utcnow()
        extraction.processing_time_ms = int((time.time() - start) * 1000)
        db.session.commit()


# ── results ────────────────────────────────────────────────────────────────────

@api.route('/uploads/<upload_id>/file', methods=['GET'])
def get_uploaded_file(upload_id):
    try:
        upload = Upload.query.get(upload_id)
        if not upload:
            return jsonify({'error': 'Upload not found', 'code': 'UPLOAD_NOT_FOUND'}), 404

        if not upload.upload_path or not os.path.exists(upload.upload_path):
            return jsonify({'error': 'Uploaded file is missing', 'code': 'FILE_MISSING'}), 404

        return send_file(upload.upload_path, as_attachment=False, download_name=upload.filename)
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'UPLOAD_FILE_ERROR'}), 500


@api.route('/results/<extraction_id>', methods=['GET'])
def get_result(extraction_id):
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404
        return jsonify(extraction.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'RETRIEVAL_ERROR'}), 500


@api.route('/results/<extraction_id>', methods=['PATCH'])
def update_result(extraction_id):
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404

        data = request.json or {}
        new_user_id = data.get('assigned_user_id')
        new_status = data.get('status')
        new_comment = data.get('comment')
        new_total_bid_price = data.get('total_bid_price')

        if new_comment is not None:
            extraction.comment = new_comment or ''

        if new_total_bid_price is not None:
            extraction.total_bid_price = str(new_total_bid_price or '')[:100]

        if new_user_id:
            user = User.query.get(new_user_id)
            if not user:
                return jsonify({'error': 'Assigned user not found', 'code': 'USER_NOT_FOUND'}), 400
            extraction.assigned_user_id = user.id
            extraction.assigned_user_name = user.name
            upload = Upload.query.get(extraction.upload_id)
            if upload:
                upload.assigned_user_id = user.id
                upload.assigned_user_name = user.name

            _send_assignment_email(user, extraction)

        if new_status:
            if new_status == 'archived':
                extraction.status = 'archived'
            else:
                valid_statuses = {'processing', 'completed', 'failed'}
                if new_status not in valid_statuses:
                    return jsonify({'error': 'Invalid status', 'code': 'INVALID_STATUS'}), 400

                if extraction.status in {'archived', 'deleted'}:
                    extraction.status = new_status
                else:
                    if not extraction.assigned_user_id:
                        return jsonify({'error': 'Status can only be updated after a user is assigned', 'code': 'UNASSIGNED_TENDER'}), 400
                    extraction.status = new_status

                if new_status == 'completed' and not extraction.completed_at:
                    extraction.completed_at = datetime.utcnow()

        db.session.commit()
        return jsonify(extraction.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'UPDATE_ERROR'}), 500


@api.route('/results/<extraction_id>/supporting-documents', methods=['POST'])
def upload_supporting_documents(extraction_id):
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404

        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({'error': 'No supporting documents provided', 'code': 'NO_SUPPORTING_FILES'}), 400

        allowed_ext = current_app.config.get(
            'ALLOWED_EXTENSIONS', {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'csv'}
        )

        folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads/'), 'supporting_documents', extraction_id)
        os.makedirs(folder, exist_ok=True)

        existing = extraction.supporting_documents or []
        saved = []

        for file in uploaded_files:
            if not file or not file.filename:
                continue
            if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_ext:
                continue

            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(folder, unique_name)
            file.save(file_path)

            saved.append({
                'id': str(uuid.uuid4()),
                'name': filename,
                'path': file_path,
                'size': os.path.getsize(file_path),
                'uploaded_at': datetime.utcnow().isoformat(),
            })

        extraction.supporting_documents = existing + saved
        db.session.commit()

        return jsonify({'supporting_documents': extraction.supporting_documents or []}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SUPPORTING_DOCUMENTS_ERROR'}), 500


@api.route('/results/<extraction_id>/supporting-documents/<document_id>', methods=['GET'])
def download_supporting_document(extraction_id, document_id):
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404

        document = None
        for item in extraction.supporting_documents or []:
            if str(item.get('id')) == str(document_id):
                document = item
                break

        if not document or not document.get('path'):
            return jsonify({'error': 'Supporting document not found', 'code': 'DOCUMENT_NOT_FOUND'}), 404

        absolute_path = document['path']
        if not os.path.exists(absolute_path):
            return jsonify({'error': 'Supporting document does not exist on disk', 'code': 'DOCUMENT_MISSING'}), 404

        return send_file(absolute_path, as_attachment=True, download_name=document.get('name', 'supporting_document'))
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'DOCUMENT_DOWNLOAD_ERROR'}), 500


@api.route('/results/<extraction_id>/supporting-documents/<document_id>', methods=['DELETE'])
def delete_supporting_document(extraction_id, document_id):
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404

        remaining = []
        for item in extraction.supporting_documents or []:
            if str(item.get('id')) != str(document_id):
                remaining.append(item)
            elif item.get('path') and os.path.exists(item['path']):
                try:
                    os.remove(item['path'])
                except OSError:
                    pass

        extraction.supporting_documents = remaining
        db.session.commit()
        return jsonify({'supporting_documents': extraction.supporting_documents or []}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'DOCUMENT_DELETE_ERROR'}), 500


@api.route('/users', methods=['GET'])
def list_users():
    try:
        users = User.query.order_by(User.name).all()
        return jsonify([u.to_dict() for u in users]), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'LIST_USERS_ERROR'}), 500


@api.route('/results', methods=['GET'])
def list_results():
    try:
        page   = request.args.get('page', 1, type=int)
        limit  = request.args.get('limit', 20, type=int)
        search = request.args.get('search', '', type=str).strip()
        status = request.args.get('status', '', type=str).strip()
        assigned_user_id = request.args.get('assigned_user_id', '', type=str).strip()

        query = Extraction.query
        if search:
            query = query.filter(
                Extraction.tender_name.ilike(f'%{search}%') |
                Extraction.tender_id.ilike(f'%{search}%') |
                Extraction.organization.ilike(f'%{search}%')
            )
        if status:
            if status == 'deleted_archived':
                query = query.filter(Extraction.status.in_(['deleted', 'archived']))
            else:
                query = query.filter(Extraction.status == status)
        else:
            query = query.filter(~Extraction.status.in_(['deleted', 'archived']))
        if assigned_user_id:
            if assigned_user_id == 'unassigned':
                query = query.filter((Extraction.assigned_user_id.is_(None)) | (Extraction.assigned_user_id == ''))
            else:
                query = query.filter(Extraction.assigned_user_id == assigned_user_id)

        total   = query.count()
        results = query.order_by(Extraction.created_at.desc()).paginate(page=page, per_page=limit)

        rows = []
        for r in results.items:
            upload = Upload.query.get(r.upload_id)
            rows.append({
                'extraction_id': r.id,
                'upload_id':     r.upload_id,
                'filename':      upload.filename if upload else 'unknown',
                'status':        r.status,
                'tender_name':   r.tender_name or 'Untitled Tender',
                'organization':  r.organization,
                'closing_date':  r.closing_date.isoformat() if r.closing_date else None,
                'closing_date_formatted': r.closing_date_formatted,
                'assigned_user_name': r.assigned_user_name,
                'comment':       r.comment or '',
                'total_bid_price': r.total_bid_price or '',
                'created_at':    r.created_at.isoformat(),
            })

        return jsonify({'total': total, 'page': page, 'limit': limit, 'results': rows}), 200

    except Exception as e:
        return jsonify({'error': str(e), 'code': 'LIST_ERROR'}), 500


# ── export ─────────────────────────────────────────────────────────────────────

@api.route('/export/<extraction_id>', methods=['GET'])
def export_result(extraction_id):
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404

        fmt = request.args.get('format', 'json', type=str).lower()
        if fmt == 'csv':
            return _export_csv(extraction)
        elif fmt == 'json':
            return jsonify(extraction.to_dict())
        else:
            return jsonify({'error': 'Unsupported format', 'code': 'INVALID_FORMAT'}), 400

    except Exception as e:
        return jsonify({'error': str(e), 'code': 'EXPORT_ERROR'}), 500


def _export_csv(extraction):
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Field', 'Value'])
    data = extraction.to_dict().get('extracted_data', {})
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False)
        writer.writerow([key, value if value is not None else ''])

    bytes_buf = BytesIO(buf.getvalue().encode('utf-8-sig'))  # utf-8-sig adds BOM for Excel
    bytes_buf.seek(0)
    return send_file(
        bytes_buf,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'extraction_{extraction.id}.csv',
    )


# ── delete ─────────────────────────────────────────────────────────────────────

@api.route('/results/<extraction_id>', methods=['DELETE'])
def delete_result(extraction_id):
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404

        extraction.status = 'deleted'
        extraction.error_message = 'Tender deleted by user'

        upload = Upload.query.get(extraction.upload_id)
        if upload:
            upload.status = 'deleted'

        db.session.commit()
        return '', 204

    except Exception as e:
        return jsonify({'error': str(e), 'code': 'DELETE_ERROR'}), 500


# ── health ─────────────────────────────────────────────────────────────────────

@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200
