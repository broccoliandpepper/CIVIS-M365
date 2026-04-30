"""
Tests for health check endpoint
"""

import pytest
from test_utils import APITestHelper, HEALTH_ENDPOINT


class TestHealth:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Health check returns 200 on success"""
        response = client.get(HEALTH_ENDPOINT)
        data = APITestHelper.assert_success(response, 200)
        
        # Verify structure
        assert "status" in data
        assert "databases" in data
        assert data["status"] in ["healthy", "warning", "unhealthy"]
    
    def test_health_check_includes_timestamp(self, client):
        """Health check includes timestamp"""
        response = client.get(HEALTH_ENDPOINT)
        data = APITestHelper.assert_success(response, 200)
        
        assert "timestamp" in data
        assert data["timestamp"] is not None
    
    def test_health_check_database_status(self, client):
        """Health check includes database status"""
        response = client.get(HEALTH_ENDPOINT)
        data = APITestHelper.assert_success(response, 200)
        
        # Verify database section
        assert isinstance(data["databases"], dict)
        
        # Each database should have status
        for db_name, db_status in data["databases"].items():
            assert isinstance(db_status, dict)
            if "status" in db_status:
                assert db_status["status"] in ["connected", "error"]
    
    def test_health_check_no_auth_required(self, client):
        """Health check is accessible without authentication"""
        # No headers or auth provided
        response = client.get(HEALTH_ENDPOINT)
        assert response.status_code in [200, 503]  # May be 503 if DB unavailable
