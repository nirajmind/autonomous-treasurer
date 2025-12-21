"""pytest configuration for Autonomous Treasurer"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_path))

import pytest
from dotenv import load_dotenv

# Load test environment
load_dotenv(backend_path / ".env.test")


@pytest.fixture(scope="session")
def test_client():
    """Create test client"""
    from fastapi.testclient import TestClient
    from app import app
    return TestClient(app)


@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    from finance.database import engine, Base, SessionLocal
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    yield db
    db.close()
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Transaction scoped session"""
    transaction = test_db.begin()
    yield test_db
    transaction.rollback()


@pytest.fixture
def auth_token(test_client):
    """Get JWT token for testing"""
    response = test_client.post(
        "/token",
        data={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]
