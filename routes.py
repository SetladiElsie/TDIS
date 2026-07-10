from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import os
import csv
import json
from io import StringIO
import time

from models import db, Upload, Extraction
from extraction import (
    extract_text_from_file,
    extract_closing_date,
    extract_scope_of_work,
    extract_evaluation_criteria,
    extract_submission_details,
    extract_deliverables,
    extract_compulsory_documents,
    extract_tender_id,
    extract_tender_name,
    extract_organization,
    extract_budget,
    extract_contact_info,
    extract_location,
    extract_duration,
)

api = Blueprint('api', __name__, url_prefix='/api')

def allowed_file(filename, allowed_extensions):
    """Check if file type is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@api.route('/upload', methods=['POST'])
def upload_file():
    """Upload tender document"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'code': 'NO_FILE'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'code': 'NO_FILE_SELECTED'}), 400
        
        # Get allowed extensions from config
        from flask import current_app
        allowed_ext = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'csv'})
        
        if not allowed_file(file.filename, allowed_ext):
            return jsonify({
                'error': 'File format not supported',
                'code': 'UNSUPPORTED_FORMAT',
                'details': f'Supported formats: {", ".join(allowed_ext)}'
            }), 415
        
        # Create uploads folder if it doesn't exist
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file with unique name
        upload_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        upload_path = os.path.join(upload_folder, f"{upload_id}_{filename}")
        file.save(upload_path)
        
        # Create upload record
        upload = Upload(
            id=upload_id,
            filename=filename,
            file_type=file.content_type,
            file_size=os.path.getsize(upload_path),
            upload_path=upload_path,
            status='uploaded'
        )
        db.session.add(upload)
        db.session.commit()
        
        return jsonify({
            'upload_id': upload_id,
            'filename': filename,
            'file_type': file.content_type,
            'upload_timestamp': datetime.utcnow().isoformat(),
            'file_size': os.path.getsize(upload_path),
            'status': 'uploaded'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'UPLOAD_ERROR'}), 500

@api.route('/extract', methods=['POST'])
def extract_information():
    """Extract tender information from uploaded document"""
    try:
        data = request.json
        upload_id = data.get('upload_id')
        
        if not upload_id:
            return jsonify({'error': 'upload_id is required', 'code': 'MISSING_UPLOAD_ID'}), 400
        
        # Get upload record
        upload = Upload.query.get(upload_id)
        if not upload:
            return jsonify({'error': 'Upload not found', 'code': 'UPLOAD_NOT_FOUND'}), 404
        
        # Create extraction record
        extraction_id = str(uuid.uuid4())
        extraction = Extraction(
            id=extraction_id,
            upload_id=upload_id,
            status='processing'
        )
        db.session.add(extraction)
        db.session.commit()
        
        # Process in background (synchronous for now, can use Celery later)
        process_extraction(extraction_id, upload_id, upload.upload_path)
        
        return jsonify({
            'extraction_id': extraction_id,
            'upload_id': upload_id,
            'status': 'processing',
            'created_at': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'EXTRACTION_ERROR'}), 500

def process_extraction(extraction_id, upload_id, upload_path):
    """Process extraction of tender information"""
    start_time = time.time()
    extraction = Extraction.query.get(extraction_id)
    
    try:
        # Detect file type from path
        file_ext = upload_path.rsplit('.', 1)[-1].lower() if '.' in upload_path else 'txt'
        
        # Extract text from document
        text = extract_text_from_file(upload_path, file_ext)
        
        # Extract all information
        extraction.tender_id = extract_tender_id(text)
        extraction.tender_name = extract_tender_name(text)
        extraction.organization = extract_organization(text)
        extraction.scope_of_work = extract_scope_of_work(text)
        
        # Parse closing date
        closing_date_str = extract_closing_date(text)
        if closing_date_str:
            try:
                extraction.closing_date_formatted = closing_date_str
                # Try to parse the date (simple parsing for common formats)
                extraction.closing_date = parse_date(closing_date_str)
            except:
                extraction.closing_date_formatted = closing_date_str
        
        extraction.budget_amount = extract_budget(text)
        
        # Extract contact info
        email, phone = extract_contact_info(text)
        extraction.contact_email = email
        extraction.contact_phone = phone
        
        extraction.location = extract_location(text)
        extraction.estimated_duration = extract_duration(text)
        extraction.submission_format = extract_submission_details(text)
        
        # Extract complex fields
        extraction.evaluation_criteria = extract_evaluation_criteria(text)
        extraction.deliverables = extract_deliverables(text)
        extraction.compulsory_documents = extract_compulsory_documents(text)
        extraction.key_requirements = extract_compulsory_documents(text)  # Can be customized
        
        # Set confidence scores (placeholder - can be improved with ML)
        extraction.confidence_scores = {
            'tender_id': 0.95 if extraction.tender_id else 0.0,
            'closing_date': 0.92 if extraction.closing_date else 0.0,
            'scope_of_work': 0.88 if extraction.scope_of_work else 0.0,
            'budget': 0.85 if extraction.budget_amount else 0.0,
        }
        
        extraction.status = 'completed'
        extraction.completed_at = datetime.utcnow()
        extraction.processing_time_ms = int((time.time() - start_time) * 1000)
        
        db.session.commit()
    
    except Exception as e:
        extraction.status = 'failed'
        extraction.error_message = str(e)
        extraction.completed_at = datetime.utcnow()
        extraction.processing_time_ms = int((time.time() - start_time) * 1000)
        db.session.commit()

def parse_date(date_str):
    """Parse date string to datetime object"""
    # Try common date formats
    formats = [
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None

@api.route('/results/<extraction_id>', methods=['GET'])
def get_result(extraction_id):
    """Get extraction results"""
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404
        
        return jsonify(extraction.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'RETRIEVAL_ERROR'}), 500

@api.route('/results', methods=['GET'])
def list_results():
    """List all extraction results with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search = request.args.get('search', '', type=str)
        status = request.args.get('status', '', type=str)
        
        query = Extraction.query
        
        # Apply filters
        if search:
            query = query.filter(
                (Extraction.tender_name.ilike(f'%{search}%')) |
                (Extraction.tender_id.ilike(f'%{search}%')) |
                (Extraction.organization.ilike(f'%{search}%'))
            )
        
        if status:
            query = query.filter(Extraction.status == status)
        
        # Count total
        total = query.count()
        
        # Paginate
        results = query.order_by(Extraction.created_at.desc()).paginate(page=page, per_page=limit)
        
        return jsonify({
            'total': total,
            'page': page,
            'limit': limit,
            'results': [
                {
                    'extraction_id': r.id,
                    'upload_id': r.upload_id,
                    'filename': Upload.query.get(r.upload_id).filename,
                    'status': r.status,
                    'tender_name': r.tender_name,
                    'closing_date': r.closing_date.isoformat() if r.closing_date else None,
                    'created_at': r.created_at.isoformat()
                }
                for r in results.items
            ]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'LIST_ERROR'}), 500

@api.route('/export/<extraction_id>', methods=['GET'])
def export_result(extraction_id):
    """Export extraction results"""
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404
        
        export_format = request.args.get('format', 'json', type=str).lower()
        
        if export_format == 'csv':
            return export_to_csv(extraction)
        elif export_format == 'json':
            return export_to_json(extraction)
        else:
            return jsonify({'error': 'Unsupported export format', 'code': 'INVALID_FORMAT'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'EXPORT_ERROR'}), 500

def export_to_csv(extraction):
    """Export extraction data as CSV"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header and data
    data = extraction.to_dict()['extracted_data']
    
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value)
        writer.writerow([key, value])
    
    output.seek(0)
    return send_file(
        StringIO(output.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"extraction_{extraction.id}.csv"
    )

def export_to_json(extraction):
    """Export extraction data as JSON"""
    return jsonify(extraction.to_dict())

@api.route('/results/<extraction_id>', methods=['DELETE'])
def delete_result(extraction_id):
    """Delete extraction result"""
    try:
        extraction = Extraction.query.get(extraction_id)
        if not extraction:
            return jsonify({'error': 'Extraction not found', 'code': 'EXTRACTION_NOT_FOUND'}), 404
        
        # Delete associated file if needed
        upload = Upload.query.get(extraction.upload_id)
        if upload and os.path.exists(upload.upload_path):
            os.remove(upload.upload_path)
        
        db.session.delete(extraction)
        db.session.delete(upload)
        db.session.commit()
        
        return '', 204
    
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'DELETE_ERROR'}), 500

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
