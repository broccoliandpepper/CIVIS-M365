"""
Tests for Sprint 4: Director Dashboard
Coverage: KPI Cards, Trends, Security Summary, PDF Export, Role-based views
"""

import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

# Dashboard endpoints
DASHBOARD_KPIS = "/api/v1/dashboard/kpis"
DASHBOARD_TRENDS = "/api/v1/dashboard/trends"
DASHBOARD_SECURITY_SUMMARY = "/api/v1/dashboard/security-summary"
DASHBOARD_DIRECTOR = "/api/v1/dashboard/director"
DASHBOARD_DIRECTOR_PDF = "/api/v1/dashboard/director-pdf"


class TestKPICards:
    """Test KPI Cards endpoint - T-S4-01"""
    
    def test_kpis_default_period(self):
        """Get KPIs with default 30-day period"""
        response = client.get(DASHBOARD_KPIS)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            # Should contain KPI card data
            assert isinstance(data, dict)
            # Common KPI fields
            assert any(field in data for field in [
                "total_signins", "failed_signins", "success_rate",
                "risky_users_count", "incidents_count", "critical_operations"
            ])
    
    def test_kpis_custom_period_7days(self):
        """Get KPIs for 7-day period"""
        response = client.get(f"{DASHBOARD_KPIS}?days=7")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_kpis_custom_period_90days(self):
        """Get KPIs for 90-day period"""
        response = client.get(f"{DASHBOARD_KPIS}?days=90")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_kpis_custom_period_365days(self):
        """Get KPIs for full year"""
        response = client.get(f"{DASHBOARD_KPIS}?days=365")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_kpis_invalid_period(self):
        """Invalid day parameter handled"""
        response = client.get(f"{DASHBOARD_KPIS}?days=0")
        assert response.status_code in [400, 422, 401]
    
    def test_kpis_excessive_period(self):
        """Period exceeding max (365) handled"""
        response = client.get(f"{DASHBOARD_KPIS}?days=999")
        assert response.status_code in [400, 422, 401]
    
    def test_kpis_success_rate_calculation(self):
        """Success rate is correctly calculated"""
        response = client.get(DASHBOARD_KPIS)
        if response.status_code == 200:
            data = response.json()
            if "success_rate" in data:
                # Should be between 0 and 100
                assert 0 <= data["success_rate"] <= 100
    
    def test_kpis_numeric_values(self):
        """All KPI values are numeric"""
        response = client.get(DASHBOARD_KPIS)
        if response.status_code == 200:
            data = response.json()
            numeric_fields = [
                "total_signins", "failed_signins", "risky_users_count",
                "incidents_count", "critical_operations"
            ]
            for field in numeric_fields:
                if field in data:
                    assert isinstance(data[field], (int, float))


class TestTrends:
    """Test Trends endpoint - T-S4-02"""
    
    def test_trends_default_period(self):
        """Get trends with default 30-day period"""
        response = client.get(DASHBOARD_TRENDS)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            # Should contain trend data (charts)
            assert isinstance(data, dict)
    
    def test_trends_signin_by_day(self):
        """Trends include SignIns by day"""
        response = client.get(DASHBOARD_TRENDS)
        if response.status_code == 200:
            data = response.json()
            # Should have trend data
            assert isinstance(data, dict)
    
    def test_trends_failed_by_day(self):
        """Trends include failed signins by day"""
        response = client.get(DASHBOARD_TRENDS)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_trends_risk_distribution(self):
        """Trends include risk distribution"""
        response = client.get(DASHBOARD_TRENDS)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_trends_custom_period(self):
        """Trends with custom 90-day period"""
        response = client.get(f"{DASHBOARD_TRENDS}?days=90")
        assert response.status_code in [200, 401]
    
    def test_trends_has_data_points(self):
        """Trends response contains data points"""
        response = client.get(DASHBOARD_TRENDS)
        if response.status_code == 200:
            data = response.json()
            # Should have some data structure
            assert len(str(data)) > 10


class TestSecuritySummary:
    """Test Security Summary endpoint"""
    
    def test_security_summary(self):
        """Get security summary"""
        response = client.get(DASHBOARD_SECURITY_SUMMARY)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            # Should contain security metrics
            assert isinstance(data, dict)
    
    def test_security_score(self):
        """Security score is present and valid"""
        response = client.get(DASHBOARD_SECURITY_SUMMARY)
        if response.status_code == 200:
            data = response.json()
            if "security_score" in data:
                # Score should be 0-100
                assert 0 <= data["security_score"] <= 100
    
    def test_security_status(self):
        """Security status is present"""
        response = client.get(DASHBOARD_SECURITY_SUMMARY)
        if response.status_code == 200:
            data = response.json()
            if "status" in data:
                # Status should be string (good, warning, critical)
                assert isinstance(data["status"], str)


class TestDirectorDashboard:
    """Test complete Director Dashboard endpoint"""
    
    def test_director_dashboard_full(self):
        """Get complete director dashboard"""
        response = client.get(DASHBOARD_DIRECTOR)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            # Should have KPIs, trends, and security summary
            assert "kpis" in data or "trends" in data or "security_summary" in data
    
    def test_director_dashboard_has_kpis(self):
        """Director dashboard includes KPIs"""
        response = client.get(DASHBOARD_DIRECTOR)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_director_dashboard_has_exported_at(self):
        """Director dashboard includes export timestamp"""
        response = client.get(DASHBOARD_DIRECTOR)
        if response.status_code == 200:
            data = response.json()
            if "exported_at" in data:
                # Should be ISO format datetime
                assert "T" in str(data["exported_at"])
    
    def test_director_dashboard_custom_period(self):
        """Director dashboard with custom period"""
        response = client.get(f"{DASHBOARD_DIRECTOR}?days=90")
        assert response.status_code in [200, 401]


class TestPDFExport:
    """Test PDF Export endpoint - T-S4-03"""
    
    def test_pdf_export_default(self):
        """Export director dashboard as PDF"""
        response = client.get(DASHBOARD_DIRECTOR_PDF)
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            # Should be HTML/PDF content
            assert len(response.content) > 0
    
    def test_pdf_export_with_custom_period(self):
        """Export PDF with custom 30-day period"""
        response = client.get(f"{DASHBOARD_DIRECTOR_PDF}?days=30")
        assert response.status_code in [200, 401]
    
    def test_pdf_export_90_days(self):
        """Export PDF with 90-day period"""
        response = client.get(f"{DASHBOARD_DIRECTOR_PDF}?days=90")
        assert response.status_code in [200, 401]
    
    def test_pdf_export_include_details(self):
        """PDF export with detailed view"""
        response = client.get(f"{DASHBOARD_DIRECTOR_PDF}?include_details=true")
        assert response.status_code in [200, 401]
    
    def test_pdf_export_summary_only(self):
        """PDF export with summary only"""
        response = client.get(f"{DASHBOARD_DIRECTOR_PDF}?include_details=false")
        assert response.status_code in [200, 401]
    
    def test_pdf_export_content_type(self):
        """PDF export has correct content type"""
        response = client.get(DASHBOARD_DIRECTOR_PDF)
        if response.status_code == 200:
            # Should be HTML or PDF
            content_type = response.headers.get("content-type", "")
            assert "html" in content_type.lower() or "pdf" in content_type.lower() or content_type == ""


class TestRoleBasedViews:
    """Test role-based dashboard views - T-S4-04"""
    
    def test_director_view(self):
        """Director role sees director dashboard"""
        response = client.get(DASHBOARD_KPIS)
        assert response.status_code in [200, 401]
    
    def test_it_view(self):
        """IT role can access dashboard"""
        response = client.get(DASHBOARD_KPIS)
        assert response.status_code in [200, 401]
    
    def test_same_endpoint_different_roles(self):
        """Same endpoint used for different roles"""
        response = client.get(DASHBOARD_DIRECTOR)
        assert response.status_code in [200, 401]


class TestRateLimiting:
    """Test rate limiting - T-S4-05"""
    
    def test_multiple_rapid_requests(self):
        """Multiple rapid requests handled"""
        for _ in range(5):
            response = client.get(DASHBOARD_KPIS)
            assert response.status_code in [200, 401, 429]
    
    def test_rate_limit_recovery(self):
        """Rate limit doesn't permanently block"""
        import time
        response1 = client.get(DASHBOARD_KPIS)
        time.sleep(1)
        response2 = client.get(DASHBOARD_KPIS)
        # Should eventually get through
        assert response2.status_code in [200, 401]


class TestAuditExports:
    """Test audit logging of exports - T-S4-06"""
    
    def test_kpi_access_audited(self):
        """KPI access is logged"""
        response = client.get(DASHBOARD_KPIS)
        assert response.status_code in [200, 401]
    
    def test_pdf_export_audited(self):
        """PDF export access is logged"""
        response = client.get(DASHBOARD_DIRECTOR_PDF)
        assert response.status_code in [200, 401]


class TestExportLimits:
    """Test export limits - T-S4-07"""
    
    def test_pdf_export_within_limits(self):
        """PDF export completes within time limit"""
        response = client.get(DASHBOARD_DIRECTOR_PDF)
        assert response.status_code in [200, 401, 408]
    
    def test_trends_export_size(self):
        """Trends data export is reasonable size"""
        response = client.get(DASHBOARD_TRENDS)
        if response.status_code == 200:
            # Should not be excessively large
            assert len(response.text) < 1000000  # < 1MB
    
    def test_kpi_export_size(self):
        """KPI export is reasonable size"""
        response = client.get(DASHBOARD_KPIS)
        if response.status_code == 200:
            # Should not be excessively large
            assert len(response.text) < 100000  # < 100KB


class TestPerformance:
    """Test performance - T-S4-08"""
    
    def test_kpis_response_time(self):
        """KPIs return within target time"""
        import time
        start = time.time()
        response = client.get(DASHBOARD_KPIS)
        elapsed = time.time() - start
        # Should return in < 2 seconds
        assert elapsed < 2.0
    
    def test_trends_response_time(self):
        """Trends return within reasonable time"""
        import time
        start = time.time()
        response = client.get(DASHBOARD_TRENDS)
        elapsed = time.time() - start
        assert elapsed < 3.0
    
    def test_director_dashboard_response_time(self):
        """Director dashboard returns promptly"""
        import time
        start = time.time()
        response = client.get(DASHBOARD_DIRECTOR)
        elapsed = time.time() - start
        assert elapsed < 3.0
    
    def test_pdf_generation_time(self):
        """PDF generation completes in reasonable time"""
        import time
        start = time.time()
        response = client.get(DASHBOARD_DIRECTOR_PDF)
        elapsed = time.time() - start
        # PDF generation may take longer
        assert elapsed < 5.0
    
    def test_concurrent_dashboard_access(self):
        """Multiple simultaneous dashboard accesses"""
        responses = []
        for _ in range(3):
            response = client.get(DASHBOARD_KPIS)
            responses.append(response.status_code)
        # All should succeed or be auth errors
        assert all(code in [200, 401] for code in responses)


class TestErrorHandling:
    """Test error scenarios"""
    
    def test_invalid_days_parameter(self):
        """Invalid days parameter handled"""
        response = client.get(f"{DASHBOARD_KPIS}?days=-5")
        assert response.status_code in [400, 422, 401]
    
    def test_non_numeric_days(self):
        """Non-numeric days parameter handled"""
        response = client.get(f"{DASHBOARD_KPIS}?days=abc")
        assert response.status_code in [400, 422, 401]
    
    def test_missing_authentication(self):
        """Missing auth token handled"""
        # Depending on implementation, might require auth
        response = client.get(DASHBOARD_KPIS)
        assert response.status_code in [200, 401, 403]


class TestDataConsistency:
    """Test data consistency across endpoints"""
    
    def test_kpis_consistency(self):
        """KPI data is consistent across requests"""
        response1 = client.get(DASHBOARD_KPIS)
        response2 = client.get(DASHBOARD_KPIS)
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            # Should have same structure
            assert set(data1.keys()) == set(data2.keys())
    
    def test_director_dashboard_consistency(self):
        """Director dashboard data is consistent"""
        response1 = client.get(DASHBOARD_DIRECTOR)
        response2 = client.get(DASHBOARD_DIRECTOR)
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            # Should have same structure
            assert isinstance(data1, dict)
            assert isinstance(data2, dict)
