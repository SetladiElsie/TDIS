import io
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import routes
from routes import _run_extraction
from models import db, Upload, Extraction, User
from app import create_app
from extractors import (
    extract_scope_of_work,
    extract_tender_id,
    extract_tender_name,
    extract_organization,
    extract_closing_date,
    extract_briefing_session,
)


def test_extract_scope_of_work_detects_item_specification_heading():
    sections = {
        'full': (
            'ITEM SPECIFICATIONS\n'
            'We need to supply and install the required network equipment for the project.\n'
            'The contractor must provide all installation, configuration and support services.\n'
        )
    }

    result = extract_scope_of_work(sections)

    assert result is not None
    assert 'supply and install' in result.lower()
    assert 'network equipment' in result.lower()


def test_extract_tender_id_reads_tender_no_rfq_no_and_bid_no_labels():
    text = (
        'TENDER NO: RFQ 24/2026\n'
        'DESCRIPTION: Supply and install network equipment and support services for the city\n'
        'RFQ CLOSING DATE: 31 August 2026\n'
    )

    assert extract_tender_id(text) == 'RFQ 24/2026'
    assert extract_tender_name(text) == 'Supply and install network equipment and support services for the city'


def test_extract_description_uses_tender_number_context_when_title_is_a_heading():
    text = (
        'TENDER NUMBER: 21/2026\n'
        'Description of Services: Provision of cleaning and waste management\n'
        'Closing date: 20 September 2026\n'
    )

    assert extract_tender_id(text) == '21/2026'
    assert extract_tender_name(text) == 'Provision of cleaning and waste management'


def test_extract_cover_page_organization_and_dates():
    text = (
        'CITY OF CAPE TOWN\n'
        'REQUEST FOR QUOTATION\n'
        'TENDER NO: RFQ 24/2026\n'
        'CLOSING DATE: 31 August 2026\n'
        'BRIEFING SESSION: 10 September 2026 at 10:00\n'
    )

    assert extract_organization(text) == 'CITY OF CAPE TOWN'
    assert extract_closing_date(text) == '31 August 2026'
    assert '10 September 2026' in (extract_briefing_session(text) or '')


def test_extract_scope_of_work_accepts_technical_specifications_and_terms_of_reference():
    sections = {
        'full': (
            'TECHNICAL SPECIFICATIONS\n'
            'The service provider must install and maintain the network infrastructure across all sites.\n'
            'TERMS OF REFERENCE\n'
            'The contractor shall provide all required maintenance and support for the project.\n'
        )
    }

    result = extract_scope_of_work(sections)
    assert result is not None
    assert 'install and maintain' in result.lower()
    assert 'maintenance and support' in result.lower()


def test_extract_scope_of_work_keeps_scope_text_when_followed_by_specification_headings():
    sections = {
        'full': (
            'SCOPE OF WORK\n'
            'The project requires the supply, installation, and maintenance of network infrastructure across all sites.\n'
            'TECHNICAL SPECIFICATIONS\n'
            'The contractor shall provide hardware, software, configuration, and support services.\n'
            'TERMS OF REFERENCE\n'
            'The service provider must maintain the systems for a period of twelve months.\n'
            'COMPULSORY DOCUMENTS\n'
            'CV\n'
        )
    }

    result = extract_scope_of_work(sections)
    assert result is not None
    assert 'supply, installation, and maintenance' in result.lower()
    assert 'provide hardware, software, configuration, and support services' in result.lower()
    assert 'maintain the systems for a period of twelve months' in result.lower()


def test_run_extraction_persists_expected_fields(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        upload_path = tmp_path / 'sample.txt'
        upload_path.write_text('Reference No: RFQ-001\nTender Name: Sample Tender\nClosing Date: 12 March 2026\nScope of Work: Supply and delivery of laptops.\nCompulsory Documents: CV, Tax Clearance.\nDeliverables: Laptop, Charger.\n', encoding='utf-8')

        upload = Upload(
            id='upload-1',
            filename='sample.txt',
            file_type='text/plain',
            file_size=upload_path.stat().st_size,
            upload_path=str(upload_path),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        extraction = Extraction(id='extraction-1', upload_id=upload.id, status='processing')
        db.session.add(extraction)
        db.session.commit()

        _run_extraction('extraction-1', str(upload_path))

        extracted = Extraction.query.get('extraction-1')
        assert extracted.status == 'completed'
        assert extracted.tender_id == 'RFQ-001'
        assert extracted.tender_name == 'Sample Tender'
        assert extracted.scope_of_work == 'Supply and delivery of laptops.'
        assert extracted.compulsory_documents == ['CV', 'Tax Clearance.']
        assert extracted.deliverables == ['Laptop', 'Charger.']


def test_assignment_sends_email_to_user(monkeypatch, tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        user = User(name='Test Assignee', email='test-assignee@tia-solutions.co.za')
        db.session.add(user)
        db.session.commit()

        upload = Upload(
            id='upload-3',
            filename='sample.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'sample.txt'),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        extraction = Extraction(id='extraction-3', upload_id=upload.id, status='processing')
        db.session.add(extraction)
        db.session.commit()

        sends = []

        def fake_send(user_obj, extraction_obj):
            sends.append((user_obj.email, extraction_obj.id))
            return True

        monkeypatch.setattr(routes, '_send_assignment_email', fake_send)

        client = app.test_client()
        response = client.patch(f'/api/results/{extraction.id}', json={'assigned_user_id': user.id})

        assert response.status_code == 200
        assert sends == [('test-assignee@tia-solutions.co.za', extraction.id)]


def test_update_result_persists_comment_and_total_bid_price(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        upload = Upload(
            id='upload-4',
            filename='sample.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'sample.txt'),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        extraction = Extraction(id='extraction-4', upload_id=upload.id, status='processing', assigned_user_id='user-1')
        db.session.add(extraction)
        db.session.commit()

        client = app.test_client()
        response = client.patch(
            f'/api/results/{extraction.id}',
            json={'comment': 'This bid should be reviewed for compliance.', 'total_bid_price': 'R 125000.00'}
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload['comment'] == 'This bid should be reviewed for compliance.'
        assert payload['total_bid_price'] == 'R 125000.00'


def test_list_results_can_filter_by_assigned_user(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        user = User(name='Assigned User', email='assigned@example.com')
        db.session.add(user)
        db.session.commit()

        upload_1 = Upload(
            id='upload-7',
            filename='assigned.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'assigned.txt'),
            status='uploaded',
        )
        upload_2 = Upload(
            id='upload-8',
            filename='unassigned.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'unassigned.txt'),
            status='uploaded',
        )
        db.session.add_all([upload_1, upload_2])
        db.session.commit()

        extraction_1 = Extraction(
            id='extraction-7',
            upload_id=upload_1.id,
            status='processing',
            assigned_user_id=user.id,
            assigned_user_name=user.name,
            tender_name='Assigned tender',
        )
        extraction_2 = Extraction(
            id='extraction-8',
            upload_id=upload_2.id,
            status='processing',
            tender_name='Unassigned tender',
        )
        db.session.add_all([extraction_1, extraction_2])
        db.session.commit()

        client = app.test_client()
        response = client.get('/api/results', query_string={'assigned_user_id': user.id})

        assert response.status_code == 200
        payload = response.get_json()
        assert payload['total'] == 1
        assert payload['results'][0]['tender_name'] == 'Assigned tender'


def test_delete_result_marks_tender_as_deleted_and_can_be_filtered(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        upload = Upload(
            id='upload-deleted',
            filename='sample.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'sample.txt'),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        extraction = Extraction(
            id='extraction-deleted',
            upload_id=upload.id,
            status='processing',
            tender_name='Archived and Deleted Tender',
        )
        db.session.add(extraction)
        db.session.commit()

        client = app.test_client()
        delete_response = client.delete(f'/api/results/{extraction.id}')
        assert delete_response.status_code == 204

        stored = Extraction.query.get(extraction.id)
        assert stored.status == 'deleted'
        assert upload.status == 'deleted'

        response = client.get('/api/results', query_string={'status': 'deleted_archived'})
        assert response.status_code == 200
        payload = response.get_json()
        assert payload['total'] >= 1
        tender_names = {item['tender_name'] for item in payload['results']}
        assert 'Archived and Deleted Tender' in tender_names


def test_all_status_excludes_archived_and_deleted_tenders(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        upload_live = Upload(
            id='upload-live',
            filename='live.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'live.txt'),
            status='uploaded',
        )
        upload_archived = Upload(
            id='upload-archived',
            filename='archived.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'archived.txt'),
            status='uploaded',
        )
        upload_deleted = Upload(
            id='upload-deleted-2',
            filename='deleted.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'deleted.txt'),
            status='uploaded',
        )
        db.session.add_all([upload_live, upload_archived, upload_deleted])
        db.session.commit()

        db.session.add_all([
            Extraction(id='extraction-live', upload_id=upload_live.id, status='processing', tender_name='Live Tender'),
            Extraction(id='extraction-archived', upload_id=upload_archived.id, status='archived', tender_name='Archived Tender'),
            Extraction(id='extraction-deleted-2', upload_id=upload_deleted.id, status='deleted', tender_name='Deleted Tender'),
        ])
        db.session.commit()

        client = app.test_client()

        all_response = client.get('/api/results')
        assert all_response.status_code == 200
        all_payload = all_response.get_json()
        assert all_payload['total'] == 1
        assert all_payload['results'][0]['tender_name'] == 'Live Tender'

        archived_response = client.get('/api/results', query_string={'status': 'deleted_archived'})
        assert archived_response.status_code == 200
        archived_payload = archived_response.get_json()
        assert archived_payload['total'] == 2
        assert {item['tender_name'] for item in archived_payload['results']} == {'Archived Tender', 'Deleted Tender'}


def test_update_result_can_restore_archived_or_deleted_tender(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        upload = Upload(
            id='upload-restore',
            filename='sample.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'sample.txt'),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        archived = Extraction(
            id='extraction-restore-archived',
            upload_id=upload.id,
            status='archived',
            tender_name='Archived Tender To Restore',
        )
        deleted = Extraction(
            id='extraction-restore-deleted',
            upload_id=upload.id,
            status='deleted',
            tender_name='Deleted Tender To Restore',
        )
        db.session.add_all([archived, deleted])
        db.session.commit()

        client = app.test_client()

        archived_response = client.patch(f'/api/results/{archived.id}', json={'status': 'processing'})
        assert archived_response.status_code == 200
        assert archived_response.get_json()['status'] == 'processing'

        deleted_response = client.patch(f'/api/results/{deleted.id}', json={'status': 'processing'})
        assert deleted_response.status_code == 200
        assert deleted_response.get_json()['status'] == 'processing'


def test_upload_supporting_documents_accepts_multiple_files(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        upload = Upload(
            id='upload-5',
            filename='sample.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'sample.txt'),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        extraction = Extraction(id='extraction-5', upload_id=upload.id, status='processing')
        db.session.add(extraction)
        db.session.commit()

        client = app.test_client()

        response = client.post(
            f'/api/results/{extraction.id}/supporting-documents',
            data={
                'files': [
                    (io.BytesIO(b'first document'), 'support-1.txt'),
                    (io.BytesIO(b'second document'), 'support-2.txt'),
                ]
            },
            content_type='multipart/form-data',
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload['supporting_documents']) == 2
        assert {item['name'] for item in payload['supporting_documents']} == {'support-1.txt', 'support-2.txt'}


def test_supporting_document_can_be_downloaded_and_deleted(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        upload = Upload(
            id='upload-6',
            filename='sample.txt',
            file_type='text/plain',
            file_size=1,
            upload_path=str(tmp_path / 'sample.txt'),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        extraction = Extraction(id='extraction-6', upload_id=upload.id, status='processing')
        db.session.add(extraction)
        db.session.commit()

        client = app.test_client()
        upload_response = client.post(
            f'/api/results/{extraction.id}/supporting-documents',
            data={'files': [(io.BytesIO(b'alpha content'), 'alpha.txt')]},
            content_type='multipart/form-data',
        )

        doc = upload_response.get_json()['supporting_documents'][0]
        download_response = client.get(f"/api/results/{extraction.id}/supporting-documents/{doc['id']}")

        assert download_response.status_code == 200
        assert download_response.data == b'alpha content'

        delete_response = client.delete(f"/api/results/{extraction.id}/supporting-documents/{doc['id']}")
        assert delete_response.status_code == 200
        payload = delete_response.get_json()
        assert payload['supporting_documents'] == []


def test_original_uploaded_document_is_accessible_by_upload_id(tmp_path):
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        upload_path = tmp_path / 'original_tender.pdf'
        upload_path.write_bytes(b'%PDF-1.4\nSample tender PDF\n%%EOF')

        upload = Upload(
            id='upload-7',
            filename='original_tender.pdf',
            file_type='application/pdf',
            file_size=upload_path.stat().st_size,
            upload_path=str(upload_path),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        client = app.test_client()
        response = client.get(f'/api/uploads/{upload.id}/file')

        assert response.status_code == 200
        assert response.data.startswith(b'%PDF')
        assert response.mimetype == 'application/pdf'


def test_extract_endpoint_returns_immediately(monkeypatch, tmp_path):
    app = create_app('testing')

    with app.app_context():
        db.create_all()

        upload_path = tmp_path / 'sample.txt'
        upload_path.write_text('Tender Name: Sample Tender', encoding='utf-8')

        upload = Upload(
            id='upload-2',
            filename='sample.txt',
            file_type='text/plain',
            file_size=upload_path.stat().st_size,
            upload_path=str(upload_path),
            status='uploaded',
        )
        db.session.add(upload)
        db.session.commit()

        def slow_runner(*args, **kwargs):
            time.sleep(0.3)

        monkeypatch.setattr(routes, '_run_extraction', slow_runner)

        client = app.test_client()
        started = time.perf_counter()
        response = client.post('/api/extract', json={'upload_id': upload.id})
        elapsed = time.perf_counter() - started

        assert response.status_code == 200
        payload = response.get_json()
        assert payload['extraction_id']
        assert elapsed < 0.2
