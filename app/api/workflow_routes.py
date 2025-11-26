"""
Workflow API routes for Agent Council system.

Provides endpoints for workflow execution, approval, and status.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.graph import (
    HumanAction,
    WorkflowResult,
    get_workflow_status,
    run_council_workflow,
    step_council_workflow,
)
from app.utils.exceptions import WorkflowException
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

# Create workflow router
workflow_router = APIRouter(prefix="/workflow", tags=["Workflow"])


# Request/Response models
class WorkflowStartRequest(BaseModel):
    """Request to start workflow execution."""
    session_id: str


class HumanActionRequest(BaseModel):
    """Request for human action."""
    comment: Optional[str] = None


# Endpoints

@workflow_router.post("/{session_id}/start")
@traceable(name="api_start_workflow")
async def start_workflow(session_id: str):
    """
    Start council workflow execution.
    
    Initiates workflow and runs until:
    - Awaiting human approval
    - Completed
    - Failed
    
    Args:
        session_id: Session ID to execute
        
    Returns:
        WorkflowResult with current status
    """
    try:
        logger.info("api_start_workflow", session_id=session_id)
        
        result = run_council_workflow(session_id)
        
        logger.info(
            "api_start_workflow_success",
            session_id=session_id,
            status=result.status.value
        )
        
        return result.model_dump()
        
    except WorkflowException as e:
        logger.error("api_start_workflow_failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("api_start_workflow_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@workflow_router.post("/{session_id}/approve")
async def approve_workflow(session_id: str, request: HumanActionRequest):
    """
    Approve current design and continue workflow.
    
    Args:
        session_id: Session ID
        request: Optional approval comment
        
    Returns:
        WorkflowResult with updated status
    """
    try:
        logger.info("api_approve_workflow", session_id=session_id)
        
        result = step_council_workflow(
            session_id=session_id,
            action=HumanAction.APPROVE,
            feedback=request.comment
        )
        
        logger.info(
            "api_approve_workflow_success",
            session_id=session_id,
            status=result.status.value
        )
        
        return result.model_dump()
        
    except WorkflowException as e:
        logger.error("api_approve_workflow_failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("api_approve_workflow_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@workflow_router.post("/{session_id}/revise")
async def revise_workflow(session_id: str, request: HumanActionRequest):
    """
    Request design revision and continue workflow.
    
    Args:
        session_id: Session ID
        request: Revision feedback (what to change)
        
    Returns:
        WorkflowResult with updated status
    """
    try:
        logger.info("api_revise_workflow", session_id=session_id)
        
        result = step_council_workflow(
            session_id=session_id,
            action=HumanAction.REVISE,
            feedback=request.comment or "Please revise the design based on reviewer feedback."
        )
        
        logger.info(
            "api_revise_workflow_success",
            session_id=session_id,
            status=result.status.value
        )
        
        return result.model_dump()
        
    except WorkflowException as e:
        logger.error("api_revise_workflow_failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("api_revise_workflow_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@workflow_router.get("/{session_id}/status")
async def get_status(session_id: str):
    """
    Get current workflow status.
    
    Args:
        session_id: Session ID to check
        
    Returns:
        WorkflowResult with current status
    """
    try:
        logger.debug("api_get_workflow_status", session_id=session_id)
        
        result = get_workflow_status(session_id)
        
        return result.model_dump()
        
    except WorkflowException as e:
        logger.error("api_get_workflow_status_failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("api_get_workflow_status_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@workflow_router.get("/{session_id}/deliverables")
@traceable(name="api_get_deliverables")
async def get_deliverables(session_id: str):
    """
    Get final architecture deliverables for a completed workflow.
    
    Phase 3C: Returns comprehensive deliverables bundle including:
    - Architecture summary
    - Key design decisions (ADR-style)
    - Risks and mitigations
    - FAQ items
    - Diagram descriptors (Lucid URLs or Mermaid source)
    - Complete Markdown report
    
    Only available once workflow status is COMPLETED and deliverables
    have been generated.
    
    Args:
        session_id: Session ID to retrieve deliverables for
        
    Returns:
        DeliverablesBundle as JSON
        
    Raises:
        404: Session not found or deliverables not available
        500: Internal server error
    """
    try:
        logger.info("api_get_deliverables", session_id=session_id)
        
        # Get workflow status which includes deliverables
        result = get_workflow_status(session_id)
        
        # Check if deliverables are available
        if result.deliverables is None:
            logger.warning(
                "deliverables_not_available",
                session_id=session_id,
                status=result.status.value,
            )
            raise HTTPException(
                status_code=404,
                detail=f"Deliverables not yet available. Workflow status: {result.status.value}. "
                       f"Deliverables are generated when workflow reaches completion."
            )
        
        logger.info(
            "api_get_deliverables_success",
            session_id=session_id,
            decisions_count=len(result.deliverables.decisions),
            risks_count=len(result.deliverables.risks),
            faqs_count=len(result.deliverables.faqs),
        )
        
        return result.deliverables.model_dump()
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except WorkflowException as e:
        logger.error("api_get_deliverables_failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("api_get_deliverables_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

