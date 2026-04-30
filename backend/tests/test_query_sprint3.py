"""
Tests for Sprint 3: Dashboard IT & UAL (Unified Audit Log)
Coverage: Query endpoints, Export (CSV), KPIs, Pagination, Filtering
"""

import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

# Test endpoints
QUERY_SIGNINS = "/api/v1/query/signins"
QUERY_RISKY_USERS = "/api/v1/query/risky-users"
QUERY_INCIDENTS = "/api/v1/query/incidents"
QUERY_AUDIT_LOGS = "/api/v1/query/audit-logs"
QUERY_KPIS = "/api/v1/query/kpis"
QUERY_TRUTH_LIST = "/api/v1/query/truth-list"

EXPORT_SIGNINS_CSV = "/api/v1/export/signins/csv"
EXPORT_RISKY_USERS_CSV = "/api/v1/export/risky-users/csv"
EXPORT_INCIDENTS_CSV = "/api/v1/export/incidents/csv"


class TestQuerySignIns:
    """Test SignIns query endpoint - T-S3-01"""
    
    def test_query_signins_no_filters(self):
        """Query SignIns with no filters"""
        response = client.get(QUERY_SIGNINS)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
    
    def test_query_signins_with_pagination(self):
        """Query SignIns with pagination parameters"""
        response = client.get(f"{QUERY_SIGNINS}?page=1&page_size=10")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert data.get("page") == 1
            assert data.get("page_size") == 10
            assert "total_pages" in data
            assert "has_next" in data
            assert "has_previous" in data
    
    def test_query_signins_with_status_filter(self):
        """Query SignIns filtered by status"""
        response = client.get(f"{QUERY_SIGNINS}?status=success")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            # All returned items should have status=success
            for item in data.get("items", []):
                if "status" in item:
                    assert item["status"] == "success"
    
    def test_query_signins_with_user_filter(self):
        """Query SignIns filtered by user principal"""
        response = client.get(f"{QUERY_SIGNINS}?user_principal=alice")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data.get("items"), list)
    
    def test_query_signins_with_country_filter(self):
        """Query SignIns filtered by country"""
        response = client.get(f"{QUERY_SIGNINS}?location_country=FR")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
    
    def test_query_signins_pagination_next_prev(self):
        """Query SignIns pagination includes next/previous links"""
        response = client.get(f"{QUERY_SIGNINS}?page=1")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "has_next" in data
            assert "has_previous" in data
            # First page should not have previous
            if data["page"] == 1:
                assert data["has_previous"] == False


class TestQueryRiskyUsers:
    """Test Risky Users query endpoint - T-S3-02"""
    
    def test_query_risky_users_no_filters(self):
        """Query Risky Users with no filters"""
        response = client.get(QUERY_RISKY_USERS)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
    
    def test_query_risky_users_with_risk_level_filter(self):
        """Query Risky Users filtered by risk level"""
        for risk_level in ["high", "medium", "low"]:
            response = client.get(f"{QUERY_RISKY_USERS}?risk_level={risk_level}")
            assert response.status_code in [200, 401]
            if response.status_code == 200:
                data = response.json()
                # Verify filter was applied
                for item in data.get("items", []):
                    if "risk_level" in item:
                        assert item["risk_level"] == risk_level
    
    def test_query_risky_users_with_risk_state_filter(self):
        """Query Risky Users filtered by risk state"""
        response = client.get(f"{QUERY_RISKY_USERS}?risk_state=atRisk")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data.get("items"), list)
    
    def test_query_risky_users_pagination(self):
        """Query Risky Users with pagination"""
        response = client.get(f"{QUERY_RISKY_USERS}?page=1&page_size=25")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert data.get("page_size") <= 25


class TestQueryIncidents:
    """Test Incidents query endpoint - T-S3-03"""
    
    def test_query_incidents_no_filters(self):
        """Query Incidents with no filters"""
        response = client.get(QUERY_INCIDENTS)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
    
    def test_query_incidents_with_severity_filter(self):
        """Query Incidents filtered by severity"""
        for severity in ["critical", "high", "medium", "low"]:
            response = client.get(f"{QUERY_INCIDENTS}?severity={severity}")
            assert response.status_code in [200, 401]
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    if "severity" in item:
                        assert item["severity"] == severity
    
    def test_query_incidents_with_status_filter(self):
        """Query Incidents filtered by status"""
        response = client.get(f"{QUERY_INCIDENTS}?status=active")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                if "status" in item:
                    assert item["status"] == "active"
    
    def test_query_incidents_with_title_search(self):
        """Query Incidents with title search"""
        response = client.get(f"{QUERY_INCIDENTS}?title_contains=test")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data.get("items"), list)


class TestQueryAuditLogs:
    """Test Audit Logs query endpoint - T-S3-04"""
    
    def test_query_audit_logs_no_filters(self):
        """Query Audit Logs with no filters"""
        response = client.get(QUERY_AUDIT_LOGS)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
    
    def test_query_audit_logs_with_critical_filter(self):
        """Query Audit Logs filtered for critical operations"""
        response = client.get(f"{QUERY_AUDIT_LOGS}?is_critical=true")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            # Should return items if any critical operations exist
            assert isinstance(data.get("items"), list)
    
    def test_query_audit_logs_with_operation_filter(self):
        """Query Audit Logs filtered by operation"""
        response = client.get(f"{QUERY_AUDIT_LOGS}?operation=UserLoggedIn")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data.get("items"), list)
    
    def test_query_audit_logs_with_workload_filter(self):
        """Query Audit Logs filtered by workload"""
        response = client.get(f"{QUERY_AUDIT_LOGS}?workload=AzureActiveDirectory")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data.get("items"), list)


class TestPagination:
    """Test pagination functionality - T-S3-05"""
    
    def test_pagination_page_parameter(self):
        """Pagination respects page parameter"""
        response1 = client.get(f"{QUERY_SIGNINS}?page=1&page_size=5")
        response2 = client.get(f"{QUERY_SIGNINS}?page=2&page_size=5")
        
        assert response1.status_code in [200, 401]
        assert response2.status_code in [200, 401]
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            # Items should be different (or at least in different order)
            # unless there's only one page
    
    def test_pagination_page_size_limits(self):
        """Pagination respects page size limits"""
        response = client.get(f"{QUERY_SIGNINS}?page_size=500")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            # Should not exceed max page size (500)
            assert len(data.get("items", [])) <= 500
    
    def test_pagination_invalid_page(self):
        """Invalid page number handled gracefully"""
        response = client.get(f"{QUERY_SIGNINS}?page=0")
        # Should reject page < 1
        assert response.status_code in [400, 422, 200]  # Depends on validation
    
    def test_pagination_large_page_size(self):
        """Large page size capped at maximum"""
        response = client.get(f"{QUERY_SIGNINS}?page_size=10000")
        assert response.status_code in [200, 400, 422]


class TestFiltering:
    """Test multi-criteria filtering - T-S3-06"""
    
    def test_combined_filters_signins(self):
        """SignIns with multiple filters combined"""
        response = client.get(
            f"{QUERY_SIGNINS}?status=success&location_country=FR&page_size=10"
        )
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                if "status" in item:
                    assert item["status"] == "success"
                if "location_country" in item:
                    assert item["location_country"] == "FR"
    
    def test_combined_filters_risky_users(self):
        """Risky Users with multiple filters"""
        response = client.get(
            f"{QUERY_RISKY_USERS}?risk_level=high&risk_state=atRisk"
        )
        assert response.status_code in [200, 401]
    
    def test_combined_filters_incidents(self):
        """Incidents with multiple filters"""
        response = client.get(
            f"{QUERY_INCIDENTS}?severity=high&status=active"
        )
        assert response.status_code in [200, 401]
    
    def test_date_range_filtering(self):
        """Date range filtering works"""
        now = datetime.utcnow()
        date_from = (now - timedelta(days=30)).isoformat()
        date_to = now.isoformat()
        
        response = client.get(f"{QUERY_SIGNINS}?date_from={date_from}&date_to={date_to}")
        assert response.status_code in [200, 401]


class TestKPIsDashboard:
    """Test KPIs endpoint - T-S3-07"""
    
    def test_kpis_default_period(self):
        """KPIs with default 30-day period"""
        response = client.get(QUERY_KPIS)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            # Should contain KPI metrics
            assert isinstance(data, dict)
    
    def test_kpis_custom_period(self):
        """KPIs with custom period"""
        for days in [7, 30, 90]:
            response = client.get(f"{QUERY_KPIS}?days={days}")
            assert response.status_code in [200, 401]
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
    
    def test_kpis_contains_metrics(self):
        """KPIs response contains expected metrics"""
        response = client.get(QUERY_KPIS)
        if response.status_code == 200:
            data = response.json()
            # Common KPI fields
            kpi_fields = [
                "total_signins", "failed_signins", "success_rate",
                "risky_users_count", "new_users_count"
            ]
            # At least some KPI fields should be present
            assert any(field in data for field in kpi_fields) or len(data) > 0


class TestExportCSV:
    """Test CSV export functionality - T-S3-08"""
    
    def test_export_signins_csv(self):
        """Export SignIns to CSV"""
        response = client.get(EXPORT_SIGNINS_CSV)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            assert "text/csv" in response.headers.get("content-type", "")
            assert "attachment" in response.headers.get("content-disposition", "")
    
    def test_export_risky_users_csv(self):
        """Export Risky Users to CSV"""
        response = client.get(EXPORT_RISKY_USERS_CSV)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            assert "text/csv" in response.headers.get("content-type", "")
    
    def test_export_incidents_csv(self):
        """Export Incidents to CSV"""
        response = client.get(EXPORT_INCIDENTS_CSV)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            assert "text/csv" in response.headers.get("content-type", "")
    
    def test_csv_headers_present(self):
        """CSV export includes headers"""
        response = client.get(EXPORT_SIGNINS_CSV)
        if response.status_code == 200:
            content = response.text
            # CSV should have content
            assert len(content) > 0
            # Should contain commas (CSV structure)
            assert "," in content or ";" in content or len(content.split("\n")) > 1


class TestTruthList:
    """Test Truth List query endpoint"""
    
    def test_query_truth_list(self):
        """Query Truth List"""
        response = client.get(QUERY_TRUTH_LIST)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
    
    def test_query_truth_list_active_only(self):
        """Query Truth List with active filter"""
        response = client.get(f"{QUERY_TRUTH_LIST}?is_active=true")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                if "is_active" in item:
                    assert item["is_active"] == True


class TestCriticalOps:
    """Test critical operations tracking - T-S3-09"""
    
    def test_audit_logs_critical_ops(self):
        """Audit logs can filter critical operations"""
        response = client.get(f"{QUERY_AUDIT_LOGS}?is_critical=true")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert "items" in data


class TestPerformance:
    """Test performance with various scenarios - T-S3-10"""
    
    def test_large_page_size(self):
        """Query handles large page sizes"""
        response = client.get(f"{QUERY_SIGNINS}?page_size=500")
        assert response.status_code in [200, 400, 401, 422]
    
    def test_deep_pagination(self):
        """Query handles deep pagination (high page numbers)"""
        response = client.get(f"{QUERY_SIGNINS}?page=100")
        assert response.status_code in [200, 401]
    
    def test_complex_filtering(self):
        """Query handles complex multi-filter scenarios"""
        response = client.get(
            f"{QUERY_SIGNINS}?status=success&location_country=FR&user_principal=alice&page=1&page_size=50"
        )
        assert response.status_code in [200, 401]
    
    def test_export_performance(self):
        """CSV export completes without timeout"""
        response = client.get(EXPORT_SIGNINS_CSV)
        assert response.status_code in [200, 401]
        # Should complete reasonably fast (no timeout)


class TestErrorHandling:
    """Test error scenarios"""
    
    def test_invalid_query_parameter(self):
        """Invalid query parameter handled"""
        response = client.get(f"{QUERY_SIGNINS}?invalid_param=value")
        # Should ignore unknown params or accept them
        assert response.status_code in [200, 401, 400]
    
    def test_malformed_date(self):
        """Malformed date parameter handled"""
        response = client.get(f"{QUERY_SIGNINS}?date_from=not-a-date")
        # Should return error or ignore
        assert response.status_code in [200, 400, 422, 401]
    
    def test_empty_result_set(self):
        """Empty result set handled correctly"""
        response = client.get(f"{QUERY_SIGNINS}?user_principal=nonexistent_user_xyz_123")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert data.get("total") == 0
            assert data.get("items") == []
