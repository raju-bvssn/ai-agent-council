"""
API Client for Streamlit UI.

Provides clean interface to FastAPI backend with error handling.
Supports Streamlit secrets and environment variables for configuration.
"""

import os
import requests
from typing import Any, Dict, Optional
from time import sleep

from app.utils.logging import get_logger

logger = get_logger(__name__)


def get_api_base_url_from_env() -> str:
    """
    Get API base URL from environment with fallback chain.
    
    Priority:
    1. Streamlit secrets (if available)
    2. Environment variable API_BASE_URL
    3. Default localhost
    
    Returns:
        API base URL
    """
    # Try Streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'API_BASE_URL' in st.secrets:
            url = st.secrets['API_BASE_URL']
            logger.info("api_url_from_streamlit_secrets", url=url)
            return url
    except Exception:
        pass  # Streamlit not available or secrets not configured
    
    # Try environment variable
    url = os.getenv('API_BASE_URL')
    if url:
        logger.info("api_url_from_environment", url=url)
        return url
    
    # Default
    default_url = "http://localhost:8000"
    logger.info("api_url_default", url=default_url)
    return default_url


class APIClient:
    """
    Client for Agent Council API.
    
    Handles all HTTP communication with FastAPI backend with retry logic.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for API (defaults to get_api_base_url_from_env())
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Delay in seconds between retries
        """
        self.base_url = (base_url or get_api_base_url_from_env()).rstrip("/")
        self.api_prefix = "/api/v1"
        self.timeout = 30
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.info("api_client_initialized", base_url=self.base_url)
        
    def _url(self, path: str) -> str:
        """Build full URL for API endpoint."""
        return f"{self.base_url}{self.api_prefix}{path}"
    
    def _retry_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Execute HTTP request with retry logic.
        
        Args:
            method: HTTP method (get, post, put, delete)
            url: Full URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = getattr(requests, method)(url, **kwargs)
                return response
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(
                    "api_connection_error_retry",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(
                    "api_timeout_retry",
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt < self.max_retries - 1:
                    sleep(self.retry_delay)
        
        # All retries failed
        error_msg = f"API unreachable after {self.max_retries} attempts: {str(last_exception)}"
        logger.error("api_all_retries_failed", error=error_msg)
        raise Exception(error_msg)
    
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
        response = self._retry_request(
            "get",
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
        
        response = self._retry_request(
            "post",
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
        response = self._retry_request(
            "get",
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
        response = self._retry_request(
            "get",
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
        response = self._retry_request(
            "delete",
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
        response = self._retry_request(
            "post",
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
        response = self._retry_request(
            "get",
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
        
        response = self._retry_request(
            "post",
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
        
        response = self._retry_request(
            "post",
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
        response = self._retry_request(
            "post",
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
        response = self._retry_request(
            "post",
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
        response = self._retry_request(
            "get",
            self._url("/admin/stats"),
            timeout=self.timeout
        )
        
        return self._handle_response(response)


def get_api_client(base_url: Optional[str] = None) -> APIClient:
    """
    Get API client instance with automatic URL detection.
    
    URL resolution priority:
    1. Explicitly provided base_url parameter
    2. Streamlit secrets
    3. Environment variable API_BASE_URL
    4. Default localhost:8000
    
    Args:
        base_url: Optional custom base URL (overrides all)
        
    Returns:
        APIClient instance configured for current environment
    """
    return APIClient(base_url=base_url)

