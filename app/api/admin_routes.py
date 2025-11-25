"""
Admin API routes for Agent Council system.

Provides administrative functions for managing sessions and database.
**WARNING**: These endpoints should be protected in production.
"""

from fastapi import APIRouter, HTTPException

from app.state.persistence import get_persistence_manager
from app.utils.exceptions import AgentCouncilException
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Create admin router
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@admin_router.post("/clear-sessions")
async def clear_all_sessions():
    """
    Clear all sessions from database.
    
    **WARNING**: This deletes all session data.
    
    Returns:
        Status message with count of deleted sessions
    """
    try:
        logger.warning("api_clear_all_sessions_request")
        
        persistence = get_persistence_manager()
        count = persistence.clear_all_sessions()
        
        logger.warning("api_clear_all_sessions_completed", count=count)
        
        return {
            "status": "ok",
            "message": f"Cleared {count} sessions",
            "count": count
        }
        
    except AgentCouncilException as e:
        logger.error("api_clear_all_sessions_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/reset-database")
async def reset_database():
    """
    Reset database by dropping and recreating all tables.
    
    **DANGER ZONE**: This permanently deletes ALL data.
    
    Returns:
        Status message
    """
    try:
        logger.warning("api_reset_database_request")
        
        persistence = get_persistence_manager()
        persistence.reset_database()
        
        logger.warning("api_reset_database_completed")
        
        return {
            "status": "ok",
            "message": "Database reset successfully",
            "warning": "All data has been permanently deleted"
        }
        
    except AgentCouncilException as e:
        logger.error("api_reset_database_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/stats")
async def get_admin_stats():
    """
    Get administrative statistics.
    
    Returns:
        System statistics
    """
    try:
        persistence = get_persistence_manager()
        sessions = persistence.list_sessions(limit=1000)
        
        # Count by status
        status_counts = {}
        for session in sessions:
            status = session.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_sessions": len(sessions),
            "status_breakdown": status_counts
        }
        
    except AgentCouncilException as e:
        logger.error("api_get_admin_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

