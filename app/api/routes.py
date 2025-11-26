"""
API routes for Agent Council system.

FastAPI router definitions.
"""

from fastapi import APIRouter, HTTPException, Query

from app.api.admin_routes import admin_router
from app.api.controllers import AgentController, SessionController, WorkflowController
from app.api.workflow_routes import workflow_router
from app.api.schemas import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    CreateSessionRequest,
    ErrorResponse,
    HealthResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
)
from app.utils.exceptions import AgentCouncilException, SessionNotFoundException
from app.utils.logging import get_logger

# LangSmith tracing (optional POC)
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

logger = get_logger(__name__)

# Create routers
health_router = APIRouter(prefix="/health", tags=["Health"])
session_router = APIRouter(prefix="/sessions", tags=["Sessions"])
workflow_router = APIRouter(prefix="/workflow", tags=["Workflow"])
agent_router = APIRouter(prefix="/agents", tags=["Agents"])

# Initialize controllers
session_controller = SessionController()
workflow_controller = WorkflowController()
agent_controller = AgentController()


# Health endpoints
@health_router.get("", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns application status, environment, and configuration info.
    Used by monitoring systems and deployment verification.
    """
    from app.utils.settings import get_settings
    settings = get_settings()
    
    logger.debug("health_check_request", environment=settings.env, demo_mode=settings.demo_mode)
    
    return HealthResponse(
        status="healthy",
        environment=settings.env,
        demo_mode=settings.demo_mode,
        api_base_url=settings.api_base_url
    )


# Session endpoints
@session_router.post("", response_model=SessionResponse, status_code=201)
@traceable(name="api_create_session")
async def create_session(request: CreateSessionRequest):
    """Create a new council session."""
    try:
        return session_controller.create_session(request)
    except AgentCouncilException as e:
        logger.error("create_session_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@session_router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all council sessions."""
    try:
        sessions = session_controller.list_sessions(limit=limit, offset=offset)
        return SessionListResponse(
            sessions=sessions,
            total=len(sessions),  # TODO: Phase 2 - Get actual count from DB
            limit=limit,
            offset=offset,
        )
    except AgentCouncilException as e:
        logger.error("list_sessions_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@session_router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str):
    """Get session details."""
    try:
        return session_controller.get_session(session_id)
    except SessionNotFoundException as e:
        logger.warning("session_not_found", session_id=session_id)
        raise HTTPException(status_code=404, detail=str(e))
    except AgentCouncilException as e:
        logger.error("get_session_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@session_router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """Delete a session."""
    try:
        session_controller.delete_session(session_id)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AgentCouncilException as e:
        logger.error("delete_session_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Workflow endpoints
@workflow_router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(request: WorkflowExecutionRequest):
    """Execute workflow for a session."""
    try:
        return workflow_controller.execute_workflow(request)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AgentCouncilException as e:
        logger.error("execute_workflow_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@workflow_router.get("/{session_id}/status", response_model=WorkflowExecutionResponse)
@traceable(name="api_get_workflow_status")
async def get_workflow_status(session_id: str):
    """Get workflow execution status."""
    try:
        return workflow_controller.get_workflow_status(session_id)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AgentCouncilException as e:
        logger.error("get_workflow_status_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Agent endpoints
@agent_router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(request: AgentExecutionRequest):
    """Execute a specific agent."""
    try:
        return agent_controller.execute_agent(request)
    except AgentCouncilException as e:
        logger.error("execute_agent_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Combine all routers
def get_api_router() -> APIRouter:
    """
    Get combined API router.

    Returns:
        APIRouter with all routes
    """
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(session_router)
    router.include_router(workflow_router)  # Workflow execution routes
    router.include_router(agent_router)
    router.include_router(admin_router)  # Admin routes
    return router

