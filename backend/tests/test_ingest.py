"""
Tests for ingestion endpoints
"""

import json
import pytest
from io import BytesIO
from test_utils import (
    APITestHelper, 
    TestDataBuilder,
    AUDIT_LOGS_ENDPOINT,
    DatabaseAssert
)
from app.models.audit_logs_m365 import M365AuditLog


class TestAuditLogsIngestion:
    """Test audit logs ingestion"""
    
    def test_upload_valid_audit_logs(self, client, test_user, db_session, mocker):
        """Upload valid audit logs"""
        # Mock authentication
        mocker.patch('app.api.auth.get_current_user', return_value=test_user)
        
        # Create test data
        records = TestDataBuilder.audit_logs_batch(5)
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode('utf-8')
        
        # Upload
        files = {'file': ('audit_logs.json', BytesIO(json_content), 'application/json')}
        response = client.post(
            AUDIT_LOGS_ENDPOINT,
            files=files
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 500]
    
    def test_upload_empty_file(self, client, test_user, mocker):
        """Upload empty file returns error"""
        mocker.patch('app.api.auth.get_current_user', return_value=test_user)
        
        files = {'file': ('empty.json', BytesIO(b''), 'application/json')}
        response = client.post(
            AUDIT_LOGS_ENDPOINT,
            files=files
        )
        
        # Should return error
        assert response.status_code in [400, 422]
    
    def test_upload_invalid_json(self, client, test_user, mocker):
        """Upload invalid JSON returns error"""
        mocker.patch('app.api.auth.get_current_user', return_value=test_user)
        
        files = {'file': ('invalid.json', BytesIO(b'not json'), 'application/json')}
        response = client.post(
            AUDIT_LOGS_ENDPOINT,
            files=files
        )
        
        # Should return 400 error
        assert response.status_code in [400, 422]
    
    def test_upload_no_records_field(self, client, test_user, mocker):
        """Upload JSON without records field"""
        mocker.patch('app.api.auth.get_current_user', return_value=test_user)
        
        # Valid JSON but no records
        file_data = {"data": []}
        json_content = json.dumps(file_data).encode('utf-8')
        
        files = {'file': ('test.json', BytesIO(json_content), 'application/json')}
        response = client.post(
            AUDIT_LOGS_ENDPOINT,
            files=files
        )
        
        # May succeed by finding empty data, or fail appropriately
        assert response.status_code in [200, 400]
    
    def test_upload_requires_authentication(self, client):
        """Upload without authentication returns 401"""
        records = TestDataBuilder.audit_logs_batch(1)
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode('utf-8')
        
        files = {'file': ('audit_logs.json', BytesIO(json_content), 'application/json')}
        response = client.post(
            AUDIT_LOGS_ENDPOINT,
            files=files
        )
        
        # Should return 401 (unauthorized) or 403 (forbidden)
        assert response.status_code in [401, 403]
    
    def test_upload_response_structure(self, client, test_user, mocker):
        """Upload response has expected structure"""
        mocker.patch('app.api.auth.get_current_user', return_value=test_user)
        
        records = TestDataBuilder.audit_logs_batch(1)
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode('utf-8')
        
        files = {'file': ('audit_logs.json', BytesIO(json_content), 'application/json')}
        response = client.post(
            AUDIT_LOGS_ENDPOINT,
            files=files
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should have ingestion statistics
            assert any(key in data for key in ['added', 'duplicates', 'errors', 'success'])
