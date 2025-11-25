"""
State persistence layer for Agent Council system.

Implements SQLite-based session storage for:
- Council sessions
- Workflow state
- Agent interactions
- Message history
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.graph.state_models import WorkflowState
from app.utils.exceptions import PersistenceException, SessionNotFoundException
from app.utils.logging import get_logger
from app.utils.settings import get_settings

logger = get_logger(__name__)

Base = declarative_base()


class CouncilSession(Base):
    """
    SQLAlchemy model for council sessions.
    """
    __tablename__ = "council_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    user_request = Column(Text, nullable=False)
    user_context = Column(JSON, nullable=True)
    state_data = Column(JSON, nullable=False)  # Serialized WorkflowState
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class PersistenceManager:
    """
    Manager for persisting and retrieving workflow state.

    Implements Repository Pattern for data access.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize persistence manager.

        Args:
            database_url: Database connection URL (uses settings if not provided)
        """
        settings = get_settings()
        self.database_url = database_url or settings.database_url

        # Create engine and session factory
        self.engine = create_engine(
            self.database_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        self._initialize_database()

        logger.info("persistence_manager_initialized", database_url=self.database_url)

    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("database_tables_created")
        except Exception as e:
            logger.error("database_initialization_failed", error=str(e))
            raise PersistenceException(
                f"Failed to initialize database: {str(e)}",
                details={"database_url": self.database_url}
            )

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def save_state(
        self,
        state: WorkflowState,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Save workflow state to database.

        Args:
            state: Workflow state to save
            name: Optional session name
            description: Optional session description

        Returns:
            Session ID

        Raises:
            PersistenceException: On save errors
        """
        try:
            session = self.get_session()

            # Check if session already exists
            existing = session.query(CouncilSession).filter_by(session_id=state.session_id).first()

            if existing:
                # Update existing session
                existing.status = state.status.value
                existing.state_data = state.model_dump(mode='json')
                existing.updated_at = datetime.utcnow()
                if name:
                    existing.name = name
                if description:
                    existing.description = description

                logger.info("session_updated", session_id=state.session_id)
            else:
                # Create new session
                new_session = CouncilSession(
                    session_id=state.session_id,
                    name=name,
                    description=description,
                    status=state.status.value,
                    user_request=state.user_request,
                    user_context=state.user_context,
                    state_data=state.model_dump(mode='json'),
                )
                session.add(new_session)

                logger.info("session_created", session_id=state.session_id)

            session.commit()
            session.close()

            return state.session_id

        except Exception as e:
            logger.error("save_state_failed", error=str(e), session_id=state.session_id)
            raise PersistenceException(
                f"Failed to save state: {str(e)}",
                details={"session_id": state.session_id}
            )

    def load_state(self, session_id: str) -> WorkflowState:
        """
        Load workflow state from database.

        Args:
            session_id: Session ID to load

        Returns:
            Workflow state

        Raises:
            SessionNotFoundException: If session not found
            PersistenceException: On load errors
        """
        try:
            session = self.get_session()
            council_session = session.query(CouncilSession).filter_by(session_id=session_id).first()
            session.close()

            if not council_session:
                raise SessionNotFoundException(
                    f"Session not found: {session_id}",
                    details={"session_id": session_id}
                )

            # Deserialize state
            state = WorkflowState(**council_session.state_data)

            logger.info("session_loaded", session_id=session_id)

            return state

        except SessionNotFoundException:
            raise
        except Exception as e:
            logger.error("load_state_failed", error=str(e), session_id=session_id)
            raise PersistenceException(
                f"Failed to load state: {str(e)}",
                details={"session_id": session_id}
            )

    def list_sessions(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """
        List all sessions.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of session summaries
        """
        try:
            session = self.get_session()
            sessions = (
                session.query(CouncilSession)
                .order_by(CouncilSession.updated_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            session.close()

            return [
                {
                    "session_id": s.session_id,
                    "name": s.name,
                    "description": s.description,
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                }
                for s in sessions
            ]

        except Exception as e:
            logger.error("list_sessions_failed", error=str(e))
            raise PersistenceException(f"Failed to list sessions: {str(e)}")

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session ID to delete

        Raises:
            SessionNotFoundException: If session not found
        """
        try:
            session = self.get_session()
            council_session = session.query(CouncilSession).filter_by(session_id=session_id).first()

            if not council_session:
                raise SessionNotFoundException(f"Session not found: {session_id}")

            session.delete(council_session)
            session.commit()
            session.close()

            logger.info("session_deleted", session_id=session_id)

        except SessionNotFoundException:
            raise
        except Exception as e:
            logger.error("delete_session_failed", error=str(e), session_id=session_id)
            raise PersistenceException(f"Failed to delete session: {str(e)}")


# Global persistence manager
_persistence_manager: Optional[PersistenceManager] = None


def get_persistence_manager() -> PersistenceManager:
    """
    Get global persistence manager instance.

    Returns:
        PersistenceManager singleton
    """
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = PersistenceManager()
    return _persistence_manager

