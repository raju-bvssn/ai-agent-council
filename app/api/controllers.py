"""
API controllers for Agent Council system.

Business logic for API endpoints.
Follows Clean Architecture: thin controller layer delegates to domain logic.
"""

from typing import Any

from app.api.schemas import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    CreateSessionRequest,
    SessionDetailResponse,
    SessionResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
)
from app.state.session import get_session_manager
from app.utils.exceptions import AgentCouncilException
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SessionController:
    """Controller for session operations."""

    def __init__(self):
        """Initialize session controller."""
        self.session_manager = get_session_manager()

    def create_session(self, request: CreateSessionRequest) -> SessionResponse:
        """
        Create a new council session.

        Args:
            request: Session creation request

        Returns:
            Session response
        """
        logger.info("api_create_session_request", name=request.name)

        state = self.session_manager.create_session(
            user_request=request.user_request,
            name=request.name,
            description=request.description,
            user_context=request.user_context,
        )

        return SessionResponse(
            session_id=state.session_id,
            name=request.name,
            description=request.description,
            status=state.status.value,
            created_at=state.created_at,
            updated_at=state.updated_at,
        )

    def get_session(self, session_id: str) -> SessionDetailResponse:
        """
        Get session details.

        Args:
            session_id: Session ID

        Returns:
            Detailed session response
        """
        logger.info("api_get_session_request", session_id=session_id)

        state = self.session_manager.get_session(session_id)

        return SessionDetailResponse(
            session_id=state.session_id,
            name=None,  # TODO: Fetch from persistence
            description=None,
            status=state.status.value,
            user_request=state.user_request,
            user_context=state.user_context,
            messages=[m.model_dump() for m in state.messages],
            reviews=[r.model_dump() for r in state.reviews],
            revision_count=state.revision_count,
            max_revisions=state.max_revisions,
            created_at=state.created_at,
            updated_at=state.updated_at,
        )

    def list_sessions(self, limit: int = 50, offset: int = 0) -> list[SessionResponse]:
        """
        List all sessions.

        Args:
            limit: Maximum number to return
            offset: Number to skip

        Returns:
            List of session responses
        """
        logger.info("api_list_sessions_request", limit=limit, offset=offset)

        sessions = self.session_manager.list_sessions(limit=limit, offset=offset)

        return [
            SessionResponse(
                session_id=s["session_id"],
                name=s.get("name"),
                description=s.get("description"),
                status=s["status"],
                created_at=datetime.fromisoformat(s["created_at"]),
                updated_at=datetime.fromisoformat(s["updated_at"]),
            )
            for s in sessions
        ]

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session ID
        """
        logger.info("api_delete_session_request", session_id=session_id)
        self.session_manager.delete_session(session_id)


class WorkflowController:
    """Controller for workflow operations."""

    def __init__(self):
        """Initialize workflow controller."""
        self.session_manager = get_session_manager()

    def execute_workflow(self, request: WorkflowExecutionRequest) -> WorkflowExecutionResponse:
        """
        Execute workflow for a session.

        Args:
            request: Workflow execution request

        Returns:
            Workflow execution response

        TODO: Phase 2 - Implement actual workflow execution
        """
        logger.info("api_execute_workflow_request", session_id=request.session_id)

        # Placeholder implementation
        logger.warning("workflow_execution_not_implemented")

        return WorkflowExecutionResponse(
            session_id=request.session_id,
            status="pending",
            completed=False,
            error="Workflow execution not yet implemented (Phase 2)",
        )


class AgentController:
    """Controller for agent operations."""

    def __init__(self):
        """Initialize agent controller."""
        pass

    def execute_agent(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        """
        Execute a specific agent.

        Args:
            request: Agent execution request

        Returns:
            Agent execution response

        TODO: Phase 2 - Implement agent execution
        """
        logger.info("api_execute_agent_request", agent=request.agent_role, session_id=request.session_id)

        # Placeholder implementation
        logger.warning("agent_execution_not_implemented")

        return AgentExecutionResponse(
            agent_role=request.agent_role,
            success=False,
            content="",
            error="Agent execution not yet implemented (Phase 2)",
        )


# Add missing import
from datetime import datetime

