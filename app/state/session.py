"""
Session management for Agent Council system.

Provides high-level session operations and lifecycle management.
"""

import uuid
from typing import Any, Optional

from app.graph.state_models import WorkflowState, WorkflowStatus
from app.state.persistence import get_persistence_manager
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    High-level session manager.

    Provides convenient methods for session lifecycle management.
    """

    def __init__(self):
        """Initialize session manager."""
        self.persistence = get_persistence_manager()
        logger.info("session_manager_initialized")

    def create_session(
        self,
        user_request: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        user_context: Optional[dict[str, Any]] = None,
    ) -> WorkflowState:
        """
        Create a new council session.

        Args:
            user_request: User's request/requirement
            name: Session name
            description: Session description
            user_context: Additional context

        Returns:
            Initial workflow state
        """
        session_id = str(uuid.uuid4())

        state = WorkflowState(
            session_id=session_id,
            user_request=user_request,
            user_context=user_context or {},
            status=WorkflowStatus.PENDING,
        )

        # Persist initial state
        self.persistence.save_state(state, name=name, description=description)

        logger.info("session_created", session_id=session_id, name=name)

        return state

    def get_session(self, session_id: str) -> WorkflowState:
        """
        Get session state.

        Args:
            session_id: Session ID

        Returns:
            Workflow state
        """
        return self.persistence.load_state(session_id)

    def update_session(self, state: WorkflowState) -> None:
        """
        Update session state.

        Args:
            state: Updated workflow state
        """
        self.persistence.save_state(state)
        logger.info("session_updated", session_id=state.session_id)

    def list_sessions(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """
        List all sessions.

        Args:
            limit: Maximum number to return
            offset: Number to skip

        Returns:
            List of session summaries
        """
        return self.persistence.list_sessions(limit=limit, offset=offset)

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session ID to delete
        """
        self.persistence.delete_session(session_id)
        logger.info("session_deleted", session_id=session_id)


# Global session manager
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get global session manager instance.

    Returns:
        SessionManager singleton
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

