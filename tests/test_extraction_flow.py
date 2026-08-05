import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import routes
from routes import _run_extraction
from models import db, Upload, Extraction
from app import create_app


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
