"""
Tests for API endpoints.

TODO: Phase 2 - Implement comprehensive API tests
"""

import pytest
from fastapi.testclient import TestClient

from app.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_session(client):
    """Test session creation endpoint."""
    payload = {
        "user_request": "Design a customer portal integration",
        "name": "Test Session",
        "description": "Test description"
    }

    response = client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["name"] == "Test Session"


def test_list_sessions(client):
    """Test session listing endpoint."""
    response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


# TODO: Phase 2 - Add more tests:
# - Test get session by ID
# - Test delete session
# - Test workflow execution
# - Test agent execution
# - Test error handling
# - Test validation
# - Test authentication (if added)

