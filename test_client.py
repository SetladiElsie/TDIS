"""
Simple test client for the Tender Document Extraction API
"""

import requests
import json
import time
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:5000/api"
TEST_FILE = "test_tender.pdf"  # Replace with actual test file path

class TenderAPIClient:
    """Client for interacting with the Tender API"""
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def upload_document(self, filepath):
        """Upload a tender document"""
        print(f"\n[UPLOAD] Uploading: {filepath}")
        
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/upload",
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Upload successful")
            print(f"  Upload ID: {data['upload_id']}")
            print(f"  Filename: {data['filename']}")
            print(f"  File Size: {data['file_size']} bytes")
            return data['upload_id']
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  {response.text}")
            return None
    
    def extract_information(self, upload_id):
        """Extract tender information"""
        print(f"\n[EXTRACT] Extracting information for: {upload_id}")
        
        response = self.session.post(
            f"{self.base_url}/extract",
            json={"upload_id": upload_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Extraction started")
            print(f"  Extraction ID: {data['extraction_id']}")
            print(f"  Status: {data['status']}")
            return data['extraction_id']
        else:
            print(f"✗ Extraction failed: {response.status_code}")
            print(f"  {response.text}")
            return None
    
    def get_results(self, extraction_id, max_wait=30):
        """Get extraction results with polling"""
        print(f"\n[RESULTS] Retrieving results for: {extraction_id}")
        print(f"  Polling (max {max_wait}s)...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = self.session.get(f"{self.base_url}/results/{extraction_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                
                if status == 'completed':
                    print(f"✓ Extraction completed in {data['processing_time_ms']}ms")
                    return data['extracted_data']
                elif status == 'failed':
                    print(f"✗ Extraction failed: {data['error_message']}")
                    return None
                else:
                    print(f"  Status: {status}... (waiting)")
                    time.sleep(2)
            else:
                print(f"✗ Failed to get results: {response.status_code}")
                return None
        
        print(f"✗ Timeout waiting for results")
        return None
    
    def list_results(self, page=1, limit=10, status=None):
        """List all extraction results"""
        print(f"\n[LIST] Retrieving results (page {page})")
        
        params = {'page': page, 'limit': limit}
        if status:
            params['status'] = status
        
        response = self.session.get(f"{self.base_url}/results", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total results: {data['total']}")
            print(f"  Page {data['page']} of {(data['total'] + data['limit'] - 1) // data['limit']}")
            
            for result in data['results']:
                print(f"\n  - {result['tender_name']} ({result['extraction_id'][:8]}...)")
                print(f"    Status: {result['status']}")
                print(f"    Closing Date: {result['closing_date']}")
            
            return data
        else:
            print(f"✗ Failed to list results: {response.status_code}")
            return None
    
    def export_results(self, extraction_id, format='json'):
        """Export extraction results"""
        print(f"\n[EXPORT] Exporting results as {format}")
        
        response = self.session.get(
            f"{self.base_url}/export/{extraction_id}",
            params={'format': format}
        )
        
        if response.status_code == 200:
            if format == 'json':
                data = response.json()
                print(f"✓ Export successful")
                return data
            else:
                print(f"✓ Export successful")
                return response.content
        else:
            print(f"✗ Export failed: {response.status_code}")
            return None
    
    def delete_results(self, extraction_id):
        """Delete extraction results"""
        print(f"\n[DELETE] Deleting results: {extraction_id}")
        
        response = self.session.delete(f"{self.base_url}/results/{extraction_id}")
        
        if response.status_code == 204:
            print(f"✓ Deletion successful")
            return True
        else:
            print(f"✗ Deletion failed: {response.status_code}")
            return False
    
    def health_check(self):
        """Check API health"""
        print(f"\n[HEALTH] Checking API status...")
        
        response = self.session.get(f"{self.base_url}/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API is healthy")
            print(f"  Status: {data['status']}")
            print(f"  Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"✗ API is not responding: {response.status_code}")
            return False

def print_extracted_data(data):
    """Pretty print extracted data"""
    if not data:
        print("No data to display")
        return
    
    print("\n" + "=" * 60)
    print("EXTRACTED TENDER INFORMATION")
    print("=" * 60)
    
    print(f"\nBasic Information:")
    print(f"  Tender ID: {data.get('tender_id', 'N/A')}")
    print(f"  Tender Name: {data.get('tender_name', 'N/A')}")
    print(f"  Organization: {data.get('organization', 'N/A')}")
    
    print(f"\nKey Dates:")
    print(f"  Closing Date: {data.get('closing_date_formatted', 'N/A')}")
    print(f"  Duration: {data.get('estimated_duration', 'N/A')}")
    
    print(f"\nFinancial:")
    budget = data.get('budget', {})
    print(f"  Budget: {budget.get('currency', 'N/A')} {budget.get('amount', 'N/A')}")
    
    print(f"\nLocation & Contact:")
    print(f"  Location: {data.get('location', 'N/A')}")
    print(f"  Email: {data.get('contact_email', 'N/A')}")
    print(f"  Phone: {data.get('contact_phone', 'N/A')}")
    
    print(f"\nScope of Work:")
    scope = data.get('scope_of_work', 'N/A')
    if scope:
        print(f"  {scope[:200]}..." if len(scope) > 200 else f"  {scope}")
    
    print(f"\nSubmission:")
    print(f"  Format: {data.get('submission_format', 'N/A')}")
    
    print(f"\nEvaluation Criteria:")
    for i, criterion in enumerate(data.get('evaluation_criteria', []), 1):
        print(f"  {i}. {criterion}")
    
    print(f"\nCompulsory Documents:")
    for i, doc in enumerate(data.get('compulsory_documents', []), 1):
        print(f"  {i}. {doc}")
    
    print(f"\nDeliverables:")
    for i, deliverable in enumerate(data.get('deliverables', []), 1):
        print(f"  {i}. {deliverable}")
    
    print("\n" + "=" * 60 + "\n")

def run_full_test():
    """Run a complete test workflow"""
    client = TenderAPIClient()
    
    # Check API health
    if not client.health_check():
        print("\n✗ API is not running. Please start the server first.")
        return
    
    # Check if test file exists
    if not Path(TEST_FILE).exists():
        print(f"\n✗ Test file not found: {TEST_FILE}")
        print("  Please provide a valid tender document to test with.")
        return
    
    # Test workflow
    print("\n" + "=" * 60)
    print("TENDER DOCUMENT EXTRACTION - TEST WORKFLOW")
    print("=" * 60)
    
    # 1. Upload
    upload_id = client.upload_document(TEST_FILE)
    if not upload_id:
        return
    
    # 2. Extract
    extraction_id = client.extract_information(upload_id)
    if not extraction_id:
        return
    
    # 3. Get Results
    extracted_data = client.get_results(extraction_id)
    if extracted_data:
        print_extracted_data(extracted_data)
    
    # 4. List Results
    client.list_results(limit=5)
    
    # 5. Export Results
    if extraction_id:
        client.export_results(extraction_id, format='json')

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        TEST_FILE = sys.argv[1]
    
    try:
        run_full_test()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
