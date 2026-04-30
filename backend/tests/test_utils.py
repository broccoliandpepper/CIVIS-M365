"""
Test utilities and helper functions
"""

import json
from typing import Any, Dict, Optional
from io import BytesIO
from fastapi.testclient import TestClient


class TestDataBuilder:
    """Builder for creating test data consistently"""
    
    @staticmethod
    def audit_log(
        record_type: str = "AzureActiveDirectory",
        operation: str = "UserLoggedIn",
        user_id: str = "test@example.com",
        **kwargs
    ) -> dict:
        """Build audit log record"""
        base = {
            "id": kwargs.get("id", "test-audit-001"),
            "recordType": record_type,
            "creationTime": kwargs.get("creationTime", "2024-01-15T10:30:00Z"),
            "operation": operation,
            "organizationId": kwargs.get("organizationId", "org-123"),
            "userType": kwargs.get("userType", 0),
            "userKey": kwargs.get("userKey", user_id),
            "activityDateTime": kwargs.get("activityDateTime", "2024-01-15T10:30:00Z"),
            "userId": user_id,
            "clientIP": kwargs.get("clientIP", "192.168.1.1"),
            "Workload": kwargs.get("Workload", "AzureActiveDirectory"),
        }
        base.update({k: v for k, v in kwargs.items() if k not in base})
        return base
    
    @staticmethod
    def audit_logs_batch(count: int = 5, **kwargs) -> list:
        """Build batch of audit logs"""
        return [
            TestDataBuilder.audit_log(id=f"test-audit-{i:03d}", **kwargs)
            for i in range(count)
        ]


class APITestHelper:
    """Helper for API testing"""
    
    @staticmethod
    def upload_file(
        client: TestClient,
        endpoint: str,
        file_data: Dict[str, Any],
        headers: Optional[Dict] = None
    ):
        """Upload JSON file via API"""
        json_content = json.dumps(file_data).encode('utf-8')
        files = {'file': ('test_data.json', BytesIO(json_content), 'application/json')}
        
        return client.post(
            endpoint,
            files=files,
            headers=headers or {}
        )
    
    @staticmethod
    def assert_success(response, expected_status: int = 200):
        """Assert successful response"""
        assert response.status_code == expected_status, \
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def assert_error(response, expected_status: int = 400):
        """Assert error response"""
        assert response.status_code == expected_status, \
            f"Expected error {expected_status}, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data or "message" in data
        return data


class DatabaseAssert:
    """Database assertions for testing"""
    
    @staticmethod
    def record_exists(db_session, model, **filters) -> bool:
        """Check if record exists"""
        return db_session.query(model).filter_by(**filters).first() is not None
    
    @staticmethod
    def record_count(db_session, model, **filters) -> int:
        """Count records"""
        return db_session.query(model).filter_by(**filters).count()
    
    @staticmethod
    def assert_record_created(db_session, model, **expected_fields):
        """Assert record was created with expected fields"""
        record = db_session.query(model).filter_by(**expected_fields).first()
        assert record is not None, \
            f"Record not found with filters {expected_fields}"
        return record


# Test constants
TEST_USER_EMAIL = "testuser@example.com"
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_PASSWORD = "TestPassword123!"

# API endpoints
HEALTH_ENDPOINT = "/api/v1/health"
LOGIN_ENDPOINT = "/api/v1/auth/login"
AUDIT_LOGS_ENDPOINT = "/api/v1/ingest/upload/audit-logs"
QUERY_ENDPOINT = "/api/v1/query"
DASHBOARD_ENDPOINT = "/api/v1/dashboard"
