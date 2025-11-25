"""
State management package for Agent Council system.

Provides:
- Session management
- State persistence (SQLite)
- Session lifecycle operations
"""

from app.state.persistence import (
    CouncilSession,
    PersistenceManager,
    get_persistence_manager,
)
from app.state.session import SessionManager, get_session_manager

__all__ = [
    # Persistence
    "PersistenceManager",
    "get_persistence_manager",
    "CouncilSession",
    # Session Management
    "SessionManager",
    "get_session_manager",
]

