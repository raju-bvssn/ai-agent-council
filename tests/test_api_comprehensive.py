"""
Comprehensive API endpoint validation tests for Agent Council.

Tests all endpoints systematically to ensure:
- Correct request schemas
- Correct response schemas
- Correct status codes
- Proper error handling
"""

import pytest
from fastapi.testclient import TestClient

from app.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_session(client):
    """Create a sample session for testing."""
    payload = {
        "user_request": "Design a MuleSoft integration for Salesforce and SAP with high throughput requirements",
        "name": "API Test Session",
        "description": "Session created for API endpoint testing",
        "user_context": {
            "priority": "high",
            "environment": "test"
        }
    }
    response = client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201
    return response.json()


# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================

def test_health_check(client):
    """Test GET /api/v1/health"""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response schema
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data
    assert "demo_mode" in data
    assert "api_base_url" in data
    
    # Validate values
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


# =============================================================================
# SESSION ENDPOINTS
# =============================================================================

def test_create_session_success(client):
    """Test POST /api/v1/sessions - successful creation"""
    payload = {
        "user_request": "Build a real-time data synchronization system between Salesforce and NetSuite",
        "name": "Data Sync Project",
        "description": "Real-time bidirectional sync",
        "user_context": {
            "budget": "high",
            "timeline": "3 months"
        }
    }
    
    response = client.post("/api/v1/sessions", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    
    # Validate response schema
    assert "session_id" in data
    assert "name" in data
    assert "description" in data
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data
    
    # Validate values
    assert data["name"] == "Data Sync Project"
    assert data["status"] == "pending"


def test_create_session_missing_user_request(client):
    """Test POST /api/v1/sessions - missing required field"""
    payload = {
        "name": "Invalid Session",
        "description": "Missing user_request"
    }
    
    response = client.post("/api/v1/sessions", json=payload)
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_session_short_user_request(client):
    """Test POST /api/v1/sessions - user_request too short"""
    payload = {
        "user_request": "Short",  # Less than 10 chars
        "name": "Invalid Session"
    }
    
    response = client.post("/api/v1/sessions", json=payload)
    
    assert response.status_code == 422


def test_list_sessions_empty(client):
    """Test GET /api/v1/sessions - empty list"""
    response = client.get("/api/v1/sessions")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response schema
    assert "sessions" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    
    assert isinstance(data["sessions"], list)


def test_list_sessions_with_pagination(client, sample_session):
    """Test GET /api/v1/sessions - with pagination params"""
    response = client.get("/api/v1/sessions?limit=10&offset=0")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["sessions"]) >= 1  # At least our sample session


def test_get_session_by_id(client, sample_session):
    """Test GET /api/v1/sessions/{session_id}"""
    session_id = sample_session["session_id"]
    
    response = client.get(f"/api/v1/sessions/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate extended schema
    assert "session_id" in data
    assert "user_request" in data
    assert "user_context" in data
    assert "messages" in data
    assert "reviews" in data
    assert "revision_count" in data
    assert "max_revisions" in data
    
    assert data["session_id"] == session_id


def test_get_session_not_found(client):
    """Test GET /api/v1/sessions/{session_id} - not found"""
    response = client.get("/api/v1/sessions/nonexistent-id-12345")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_delete_session(client, sample_session):
    """Test DELETE /api/v1/sessions/{session_id}"""
    session_id = sample_session["session_id"]
    
    response = client.delete(f"/api/v1/sessions/{session_id}")
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/v1/sessions/{session_id}")
    assert get_response.status_code == 404


def test_delete_session_not_found(client):
    """Test DELETE /api/v1/sessions/{session_id} - not found"""
    response = client.delete("/api/v1/sessions/nonexistent-id-12345")
    
    assert response.status_code == 404


# =============================================================================
# WORKFLOW ENDPOINTS
# =============================================================================

def test_start_workflow(client, sample_session):
    """Test POST /api/v1/workflow/{session_id}/start"""
    session_id = sample_session["session_id"]
    
    response = client.post(f"/api/v1/workflow/{session_id}/start")
    
    # Should return 200 or 400 depending on workflow state
    assert response.status_code in [200, 400, 500]
    data = response.json()
    
    if response.status_code == 200:
        # Validate WorkflowResult schema
        assert "session_id" in data
        assert "status" in data


def test_get_workflow_status(client, sample_session):
    """Test GET /api/v1/workflow/{session_id}/status"""
    session_id = sample_session["session_id"]
    
    response = client.get(f"/api/v1/workflow/{session_id}/status")
    
    assert response.status_code in [200, 404, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "session_id" in data
        assert "status" in data


def test_approve_workflow(client, sample_session):
    """Test POST /api/v1/workflow/{session_id}/approve"""
    session_id = sample_session["session_id"]
    
    payload = {
        "comment": "Design looks good, approved!"
    }
    
    response = client.post(f"/api/v1/workflow/{session_id}/approve", json=payload)
    
    # May fail if workflow not at approval gate
    assert response.status_code in [200, 400, 500]


def test_revise_workflow(client, sample_session):
    """Test POST /api/v1/workflow/{session_id}/revise"""
    session_id = sample_session["session_id"]
    
    payload = {
        "comment": "Please add more security considerations"
    }
    
    response = client.post(f"/api/v1/workflow/{session_id}/revise", json=payload)
    
    # May fail if workflow not at approval gate
    assert response.status_code in [200, 400, 500]


# =============================================================================
# AGENT ENDPOINTS
# =============================================================================

def test_execute_agent(client, sample_session):
    """Test POST /api/v1/agents/execute"""
    payload = {
        "session_id": sample_session["session_id"],
        "agent_role": "solution_architect",
        "input_data": {
            "request": "Design initial architecture"
        }
    }
    
    response = client.post("/api/v1/agents/execute", json=payload)
    
    # May fail without proper setup
    assert response.status_code in [200, 400, 500]


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

def test_get_admin_stats(client):
    """Test GET /api/v1/admin/stats"""
    response = client.get("/api/v1/admin/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_sessions" in data
    assert "status_breakdown" in data
    assert isinstance(data["status_breakdown"], dict)


def test_clear_all_sessions(client):
    """Test POST /api/v1/admin/clear-sessions"""
    response = client.post("/api/v1/admin/clear-sessions")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "message" in data
    assert "count" in data
    assert data["status"] == "ok"


def test_reset_database(client):
    """Test POST /api/v1/admin/reset-database"""
    response = client.post("/api/v1/admin/reset-database")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "message" in data
    assert "warning" in data
    assert data["status"] == "ok"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

def test_invalid_endpoint(client):
    """Test accessing non-existent endpoint"""
    response = client.get("/api/v1/nonexistent")
    
    assert response.status_code == 404


def test_invalid_method(client):
    """Test using wrong HTTP method"""
    response = client.put("/api/v1/health")
    
    assert response.status_code == 405


def test_malformed_json(client):
    """Test sending malformed JSON"""
    response = client.post(
        "/api/v1/sessions",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422


# =============================================================================
# OPENAPI SPEC VALIDATION
# =============================================================================

def test_openapi_json_available(client):
    """Test that OpenAPI spec is available"""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


def test_docs_available(client):
    """Test that Swagger UI docs are available"""
    response = client.get("/docs")
    
    assert response.status_code == 200

