"""
API Client for Streamlit UI.

Provides clean interface to FastAPI backend with error handling.
"""

import requests
from typing import Any, Dict, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


class APIClient:
    """
    Client for Agent Council API.
    
    Handles all HTTP communication with FastAPI backend.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for API (default: http://localhost:8000)
        """
        self.base_url = base_url.rstrip("/")
        self.api_prefix = "/api/v1"
        self.timeout = 30
        
    def _url(self, path: str) -> str:
        """Build full URL for API endpoint."""
        return f"{self.base_url}{self.api_prefix}{path}"
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response with error checking.
        
        Args:
            response: Response from requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            Exception: On HTTP errors
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", str(e))
            except:
                error_detail = str(e)
            
            logger.error("api_error", status_code=response.status_code, detail=error_detail)
            raise Exception(f"API Error ({response.status_code}): {error_detail}")
        except requests.exceptions.RequestException as e:
            logger.error("api_request_failed", error=str(e))
            raise Exception(f"Request failed: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = requests.get(
            self._url("/health"),
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def create_session(
        self,
        user_request: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new council session.
        
        Args:
            user_request: User's requirement
            name: Session name
            description: Session description
            user_context: Additional context
            
        Returns:
            Session data with session_id
        """
        payload = {
            "user_request": user_request,
            "name": name,
            "description": description,
            "user_context": user_context or {}
        }
        
        response = requests.post(
            self._url("/sessions"),
            json=payload,
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session details.
        
        Args:
            session_id: Session ID
            
        Returns:
            Full session data
        """
        response = requests.get(
            self._url(f"/sessions/{session_id}"),
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def list_sessions(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        List all sessions.
        
        Args:
            limit: Maximum sessions to return
            offset: Number to skip
            
        Returns:
            Session list
        """
        response = requests.get(
            self._url(f"/sessions?limit={limit}&offset={offset}"),
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete a session.
        
        Args:
            session_id: Session ID to delete
        """
        response = requests.delete(
            self._url(f"/sessions/{session_id}"),
            timeout=self.timeout
        )
        
        if response.status_code != 204:
            self._handle_response(response)
    
    def start_workflow(self, session_id: str) -> Dict[str, Any]:
        """
        Start workflow execution for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            WorkflowResult with current status
        """
        response = requests.post(
            self._url(f"/workflow/{session_id}/start"),
            timeout=60  # Workflow starts in background
        )
        
        return self._handle_response(response)
    
    def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get workflow execution status.
        
        Args:
            session_id: Session ID
            
        Returns:
            Workflow status
        """
        response = requests.get(
            self._url(f"/workflow/{session_id}/status"),
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def approve_design(self, session_id: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Approve design and continue workflow.
        
        Args:
            session_id: Session ID
            feedback: Optional approval comment
            
        Returns:
            WorkflowResult with updated status
        """
        payload = {
            "comment": feedback
        }
        
        response = requests.post(
            self._url(f"/workflow/{session_id}/approve"),
            json=payload,
            timeout=60
        )
        
        return self._handle_response(response)
    
    def request_revision(self, session_id: str, feedback: str) -> Dict[str, Any]:
        """
        Request design revision and continue workflow.
        
        Args:
            session_id: Session ID
            feedback: Revision feedback (what to change)
            
        Returns:
            WorkflowResult with updated status
        """
        payload = {
            "comment": feedback
        }
        
        response = requests.post(
            self._url(f"/workflow/{session_id}/revise"),
            json=payload,
            timeout=60
        )
        
        return self._handle_response(response)
    
    # Admin Functions
    
    def clear_all_sessions(self) -> Dict[str, Any]:
        """
        Clear all sessions from database.
        
        **WARNING**: This deletes all session data.
        
        Returns:
            Status message with count
        """
        response = requests.post(
            self._url("/admin/clear-sessions"),
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def reset_database(self) -> Dict[str, Any]:
        """
        Reset database (drop and recreate all tables).
        
        **DANGER ZONE**: This permanently deletes ALL data.
        
        Returns:
            Status message
        """
        response = requests.post(
            self._url("/admin/reset-database"),
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def get_admin_stats(self) -> Dict[str, Any]:
        """
        Get administrative statistics.
        
        Returns:
            System statistics
        """
        response = requests.get(
            self._url("/admin/stats"),
            timeout=self.timeout
        )
        
        return self._handle_response(response)


def get_api_client(base_url: Optional[str] = None) -> APIClient:
    """
    Get API client instance.
    
    Args:
        base_url: Optional custom base URL
        
    Returns:
        APIClient instance
    """
    return APIClient(base_url=base_url or "http://localhost:8000")

