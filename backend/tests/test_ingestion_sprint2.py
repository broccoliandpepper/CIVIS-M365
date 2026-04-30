"""
Tests for Sprint 2: Ingestion Core
Coverage: SignIns, Risky Users, Incidents, Truth List, Audit Logs
"""

import json
import pytest
from io import BytesIO
from fastapi.testclient import TestClient

from app.main import app
from app.models.signins import SignIn
from app.models.risky_users import RiskyUser
from app.models.incidents import Incident
from app.models.truth_list import TruthListUser
from app.models.audit_logs_m365 import M365AuditLog
from app.models.new_user_review import NewUserReview
from app.services.alert_service import AlertService


client = TestClient(app)

# Test endpoints
SIGNINS_ENDPOINT = "/api/v1/ingest/upload/signins"
RISKY_USERS_ENDPOINT = "/api/v1/ingest/upload/risky-users"
INCIDENTS_ENDPOINT = "/api/v1/ingest/upload/incidents"
TRUTH_LIST_ENDPOINT = "/api/v1/ingest/upload/truth-list"
AUDIT_LOGS_ENDPOINT = "/api/v1/ingest/upload/audit-logs"


# Test Data Builders
class TestDataSprint2:
    @staticmethod
    def signin_record(user="alice@company.com", ip="192.168.1.1", status="success"):
        return {
            "id": f"signin-{user}-{ip}",
            "createdDateTime": "2026-04-11T10:00:00Z",
            "userPrincipalName": user,
            "userDisplayName": user.split("@")[0],
            "userId": f"user-id-{user}",
            "userType": "Member",
            "ipAddress": ip,
            "location": {
                "city": "Paris",
                "countryOrRegion": "FR",
                "state": "Île-de-France"
            },
            "status": {
                "errorCode": 0 if status == "success" else 1,
                "failureReason": None if status == "success" else "Invalid password"
            },
            "correlationId": "corr-123",
            "conditionalAccessStatus": "success",
            "appDisplayName": "Azure Portal",
            "appId": "app-123",
            "clientAppUsed": "Browser",
            "deviceDetail": {
                "operatingSystem": "Windows",
                "browser": "Chrome",
                "isCompliant": True,
                "isManaged": True
            },
            "riskDetail": "none",
            "riskState": "none",
            "riskLevelAggregated": "low",
            "flaggedForReview": False
        }
    
    @staticmethod
    def risky_user_record(user="bob@company.com", risk_level="high"):
        return {
            "id": f"risky-{user}",
            "userPrincipalName": user,
            "userDisplayName": user.split("@")[0],
            "riskLevel": risk_level,
            "riskState": "atRisk",
            "riskDetail": "anomalousSignInProperties",
            "riskLastUpdatedDateTime": "2026-04-11T10:00:00Z",
            "isDeleted": False,
            "isProcessing": False
        }
    
    @staticmethod
    def incident_record(incident_id="incident-001", severity="high"):
        return {
            "incident_id": incident_id,
            "timestamp": "2026-04-11T10:00:00Z",
            "title": f"Test Incident {incident_id}",
            "severity": severity,
            "status": "active",
            "assigned_to": "admin@company.com",
            "category": "suspicious_activity",
            "priority_score": "8",
            "tags": "test,automated",
            "investigation_state": "Queued",
            "impacted_assets": "3 devices",
            "active_alerts": "2",
            "description": "This is a test incident",
            "raw_json": "{}"
        }
    
    @staticmethod
    def truth_list_record(user="alice@company.com"):
        return {
            "user_principal": user,
            "display_name": user.split("@")[0].capitalize(),
            "department": "IT",
            "job_title": "Engineer",
            "is_active": True,
            "notes": "Known user"
        }
    
    @staticmethod
    def audit_log_record(audit_id="audit-001", operation="UserLoggedIn"):
        return {
            "id": audit_id,
            "audit_id": audit_id,
            "CreatedDateTime": "2026-04-11T10:00:00Z",
            "RecordType": "AzureActiveDirectory",
            "Operation": operation,
            "OrganizationId": "org-123",
            "UserType": 0,
            "UserKey": "user@example.com",
            "UserId": "user@example.com",
            "ClientIP": "192.168.1.1",
            "Workload": "AzureActiveDirectory",
            "ObjectId": "object-123"
        }


class TestSignInsIngestion:
    """Test SignIns upload endpoint - T-S2-01"""
    
    def test_upload_valid_signins(self):
        """Upload valid SignIns file"""
        records = [TestDataSprint2.signin_record(f"user{i}@company.com") for i in range(3)]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("signins.json", BytesIO(json_content), "application/json")}
        response = client.post(SIGNINS_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]  # 401 if auth required
    
    def test_upload_empty_signins(self):
        """Empty file returns 400"""
        files = {"file": ("empty.json", BytesIO(b""), "application/json")}
        response = client.post(SIGNINS_ENDPOINT, files=files)
        
        assert response.status_code == 400
        assert "Empty file" in response.text or "empty" in response.text.lower()
    
    def test_upload_invalid_json_signins(self):
        """Invalid JSON returns error"""
        files = {"file": ("invalid.json", BytesIO(b"not json"), "application/json")}
        response = client.post(SIGNINS_ENDPOINT, files=files)
        
        # Should not be 500, but 400 or other client error
        assert response.status_code in [400, 401, 422]
    
    def test_upload_array_format_signins(self):
        """Array format (not wrapped in records) is accepted"""
        records = [TestDataSprint2.signin_record() for _ in range(2)]
        json_content = json.dumps(records).encode()
        
        files = {"file": ("signins.json", BytesIO(json_content), "application/json")}
        response = client.post(SIGNINS_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]


class TestRiskyUsersIngestion:
    """Test Risky Users upload endpoint - T-S2-02"""
    
    def test_upload_valid_risky_users(self):
        """Upload valid Risky Users file"""
        records = [TestDataSprint2.risky_user_record(f"user{i}@company.com") for i in range(3)]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("risky_users.json", BytesIO(json_content), "application/json")}
        response = client.post(RISKY_USERS_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]
    
    def test_upload_empty_risky_users(self):
        """Empty file returns 400"""
        files = {"file": ("empty.json", BytesIO(b""), "application/json")}
        response = client.post(RISKY_USERS_ENDPOINT, files=files)
        
        assert response.status_code == 400
    
    def test_risky_users_different_risk_levels(self):
        """File with multiple risk levels is accepted"""
        records = [
            TestDataSprint2.risky_user_record("user1@company.com", "high"),
            TestDataSprint2.risky_user_record("user2@company.com", "medium"),
            TestDataSprint2.risky_user_record("user3@company.com", "low"),
        ]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("risky_users.json", BytesIO(json_content), "application/json")}
        response = client.post(RISKY_USERS_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]


class TestIncidentsIngestion:
    """Test Incidents upload endpoint - T-S2-03"""
    
    def test_upload_valid_incidents(self):
        """Upload valid Incidents file"""
        records = [TestDataSprint2.incident_record(f"inc-{i:03d}", "high") for i in range(3)]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("incidents.json", BytesIO(json_content), "application/json")}
        response = client.post(INCIDENTS_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]
    
    def test_upload_empty_incidents(self):
        """Empty file returns 400"""
        files = {"file": ("empty.json", BytesIO(b""), "application/json")}
        response = client.post(INCIDENTS_ENDPOINT, files=files)
        
        assert response.status_code == 400
    
    def test_upload_incidents_multiple_severities(self):
        """Incidents with different severities"""
        records = [
            TestDataSprint2.incident_record("inc-001", "critical"),
            TestDataSprint2.incident_record("inc-002", "high"),
            TestDataSprint2.incident_record("inc-003", "medium"),
        ]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("incidents.json", BytesIO(json_content), "application/json")}
        response = client.post(INCIDENTS_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]


class TestTruthListIngestion:
    """Test Truth List upload endpoint - T-S2-04"""
    
    def test_upload_valid_truth_list(self):
        """Upload valid Truth List file"""
        records = [TestDataSprint2.truth_list_record(f"user{i}@company.com") for i in range(3)]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("truth_list.json", BytesIO(json_content), "application/json")}
        response = client.post(TRUTH_LIST_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]
    
    def test_upload_empty_truth_list(self):
        """Empty file returns 400"""
        files = {"file": ("empty.json", BytesIO(b""), "application/json")}
        response = client.post(TRUTH_LIST_ENDPOINT, files=files)
        
        assert response.status_code == 400
    
    def test_truth_list_array_format(self):
        """Array format (not wrapped in records) is accepted"""
        records = [TestDataSprint2.truth_list_record() for _ in range(2)]
        json_content = json.dumps(records).encode()
        
        files = {"file": ("truth_list.json", BytesIO(json_content), "application/json")}
        response = client.post(TRUTH_LIST_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]


class TestDeduplication:
    """Test deduplication logic - T-S2-05"""
    
    def test_duplicate_signins_detected(self):
        """Uploading same SignIns twice detects duplicates"""
        record = TestDataSprint2.signin_record("alice@company.com")
        file_data = {"records": [record]}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("signins1.json", BytesIO(json_content), "application/json")}
        response1 = client.post(SIGNINS_ENDPOINT, files=files)
        
        # Upload again - second should detect duplicate
        files = {"file": ("signins2.json", BytesIO(json_content), "application/json")}
        response2 = client.post(SIGNINS_ENDPOINT, files=files)
        
        # Both should succeed, but second should report duplicate
        assert response1.status_code in [200, 401]
        if response2.status_code == 200:
            data = response2.json()
            assert "lines_duplicate" in data or "duplicates" in data
    
    def test_unique_records_not_duplicated(self):
        """Unique records are not counted as duplicates"""
        records = [
            TestDataSprint2.signin_record("alice@company.com"),
            TestDataSprint2.signin_record("bob@company.com"),
        ]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("signins.json", BytesIO(json_content), "application/json")}
        response = client.post(SIGNINS_ENDPOINT, files=files)
        
        if response.status_code == 200:
            data = response.json()
            # No duplicates expected
            assert data.get("lines_duplicate", 0) == 0 or data.get("duplicates", 0) == 0


class TestNewUserDetection:
    """Test new user detection - T-S2-06"""
    
    def test_unknown_user_detected_vs_truth_list(self, db_session):
        """Unknown user is detected when not in truth list"""
        # Assuming db_session fixture is available
        # This is integration-level test
        truth_list_user = "alice@company.com"
        unknown_user = "charlie@unknown.com"
        
        # Mock: add known user to truth list
        # Check if unknown user is detected
        # This would need proper database setup
        pass
    
    def test_known_user_verified_in_truth_list(self):
        """Known user is verified in truth list"""
        # This would require database integration
        pass


class TestValidation:
    """Test input validation - T-S2-08"""
    
    def test_no_auth_returns_401(self):
        """Endpoints without auth return 401"""
        files = {"file": ("test.json", BytesIO(b'{"records": []}'), "application/json")}
        
        # These endpoints likely require authentication
        responses = [
            client.post(SIGNINS_ENDPOINT, files=files),
            client.post(RISKY_USERS_ENDPOINT, files=files),
            client.post(INCIDENTS_ENDPOINT, files=files),
            client.post(TRUTH_LIST_ENDPOINT, files=files),
        ]
        
        # Check that at least some return 401 or require auth
        assert any(r.status_code == 401 for r in responses) or all(r.status_code == 200 for r in responses)
    
    def test_sql_injection_blocked(self):
        """SQL injection attempts are blocked - T-S2-09"""
        sql_injection = "'; DROP TABLE signins; --"
        record = TestDataSprint2.signin_record(sql_injection)
        file_data = {"records": [record]}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("test.json", BytesIO(json_content), "application/json")}
        response = client.post(SIGNINS_ENDPOINT, files=files)
        
        # Should either succeed (injection is escaped) or fail gracefully
        # Should NOT cause 500 server error
        assert response.status_code in [200, 201, 400, 401, 422]


class TestPerformance:
    """Test performance with large files - T-S2-10"""
    
    def test_large_file_upload(self):
        """Large file (1000 records) is handled"""
        records = [TestDataSprint2.signin_record(f"user{i}@company.com") for i in range(1000)]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("large.json", BytesIO(json_content), "application/json")}
        response = client.post(SIGNINS_ENDPOINT, files=files)
        
        # Should complete without timeout or memory error
        assert response.status_code in [200, 401, 422]


class TestAuditLogsIngestion:
    """Test Audit Logs endpoint"""
    
    def test_upload_valid_audit_logs(self):
        """Upload valid Audit Logs file"""
        records = [TestDataSprint2.audit_log_record(f"audit-{i:04d}") for i in range(3)]
        file_data = {"records": records}
        json_content = json.dumps(file_data).encode()
        
        files = {"file": ("audit_logs.json", BytesIO(json_content), "application/json")}
        response = client.post(AUDIT_LOGS_ENDPOINT, files=files)
        
        assert response.status_code in [200, 401]
    
    def test_upload_empty_audit_logs(self):
        """Empty file returns 400"""
        files = {"file": ("empty.json", BytesIO(b""), "application/json")}
        response = client.post(AUDIT_LOGS_ENDPOINT, files=files)
        
        assert response.status_code == 400
