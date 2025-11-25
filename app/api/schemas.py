"""
API schemas for Agent Council system.

Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"


class CreateSessionRequest(BaseModel):
    """Request to create a new council session."""
    user_request: str = Field(..., min_length=10, description="User's requirement or request")
    name: Optional[str] = Field(None, max_length=255, description="Session name")
    description: Optional[str] = Field(None, description="Session description")
    user_context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class SessionResponse(BaseModel):
    """Response containing session information."""
    session_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class SessionDetailResponse(SessionResponse):
    """Detailed session response with full state."""
    user_request: str
    user_context: dict[str, Any]
    messages: list[dict[str, Any]]
    reviews: list[dict[str, Any]]
    revision_count: int
    max_revisions: int


class SessionListResponse(BaseModel):
    """Response containing list of sessions."""
    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int


class AgentExecutionRequest(BaseModel):
    """Request to execute a specific agent."""
    session_id: str
    agent_role: str
    input_data: dict[str, Any] = Field(default_factory=dict)


class AgentExecutionResponse(BaseModel):
    """Response from agent execution."""
    agent_role: str
    success: bool
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class WorkflowExecutionRequest(BaseModel):
    """Request to execute workflow."""
    session_id: str
    stream: bool = Field(default=False, description="Stream updates")


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution."""
    session_id: str
    status: str
    completed: bool
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

