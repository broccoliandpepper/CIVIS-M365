"""
Pytest configuration and fixtures for SIEM M365 testing
"""

import os
import json
import tempfile
from typing import Generator
import pytest
from sqlalchemy import create_engine, Event, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import Base
from app.models.auth import User
from app.models.audit_logs_m365 import M365AuditLog
from app.models.incidents import Incident


# Test database setup
@pytest.fixture(scope="session")
def test_db_path():
    """Create temporary database path for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture(scope="session")
def test_db_url(test_db_path):
    """SQLite test database URL"""
    return f"sqlite:///{test_db_path}"


@pytest.fixture(scope="session")
def engine(test_db_url):
    """Create test database engine"""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# Authentication fixtures
@pytest.fixture
def test_user(db_session) -> User:
    """Create test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_test_password"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_admin(db_session) -> User:
    """Create test admin user"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_admin_password",
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    return user


# Sample data fixtures
@pytest.fixture
def sample_audit_log() -> dict:
    """Sample M365 audit log record"""
    return {
        "id": "test-id-001",
        "recordType": "AzureActiveDirectory",
        "creationTime": "2024-01-15T10:30:00Z",
        "operation": "UserLoggedIn",
        "organizationId": "org-123",
        "userType": 0,
        "userKey": "user@example.com",
        "activityDateTime": "2024-01-15T10:30:00Z",
        "userId": "user@example.com",
        "clientIP": "192.168.1.1",
        "Workload": "AzureActiveDirectory",
        "ObjectId": "object-123",
        "actor": [
            {
                "ID": "user@example.com",
                "Type": 1
            }
        ],
        "ActorContextId": "context-123",
        "InterSystemsId": "inter-sys-123",
        "Target": [
            {
                "ID": "resource-123",
                "Type": 1
            }
        ]
    }


@pytest.fixture
def sample_audit_logs_file(tmp_path, sample_audit_log):
    """Create temporary audit logs JSON file"""
    records = [
        {**sample_audit_log, "id": f"test-id-{i:03d}"}
        for i in range(10)
    ]
    
    file_path = tmp_path / "audit_logs.json"
    with open(file_path, 'w') as f:
        json.dump({"records": records}, f)
    
    return file_path


@pytest.fixture
def sample_incident(db_session, test_user) -> Incident:
    """Create sample security incident"""
    incident = Incident(
        title="Test Security Incident",
        description="Test incident for unit testing",
        severity="high",
        status="open",
        created_by=test_user.id,
        source="SIEM"
    )
    db_session.add(incident)
    db_session.commit()
    return incident


# HTTP Client fixture
@pytest.fixture
def client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


# Mock dependencies
@pytest.fixture
def mock_get_current_user(test_user):
    """Override current_user dependency"""
    async def mock_user():
        return test_user
    return mock_user


@pytest.fixture
def mock_get_db(db_session):
    """Override database session dependency"""
    def get_db():
        yield db_session
    return get_db
