"""
Phase 3C workflow nodes for deliverables generation.

Defines LangGraph nodes for generating final architecture deliverables.
"""

from typing import Dict, Any
import structlog

from app.graph.state_models import WorkflowState, WorkflowStatus
from app.graph.deliverables.service import build_deliverables_bundle
from app.tools.lucid_client import LucidClient
from app.utils.settings import get_settings

logger = structlog.get_logger(__name__)


def generate_deliverables_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Generate final deliverables bundle from completed workflow.
    
    Phase 3C: Creates comprehensive architecture deliverables including:
    - Architecture summary
    - Decision records (ADR-style)
    - Risks and mitigations
    - FAQ items
    - Diagram descriptors (Lucid or Mermaid)
    - Complete Markdown report
    
    This node runs after consensus/adjudication and before final workflow completion.
    It's deterministic and idempotent - can be re-run safely.
    
    Args:
        state: Current workflow state (should be near completion)
        
    Returns:
        State update dict with deliverables bundle
    """
    logger.info(
        "generate_deliverables_node_start",
        session_id=state.session_id,
        status=state.status.value,
    )
    
    try:
        settings = get_settings()
        
        # Initialize Lucid client if configured
        lucid_client = None
        if not settings.demo_mode:
            try:
                lucid_client = LucidClient()
                logger.info("lucid_client_initialized", demo_mode=False)
            except Exception as e:
                logger.warning("lucid_client_init_failed", error=str(e))
                lucid_client = None
        
        # Build deliverables bundle
        logger.info("building_deliverables_bundle", session_id=state.session_id)
        deliverables = build_deliverables_bundle(
            state=state,
            lucid_client=lucid_client,
            demo_mode=settings.demo_mode,
        )
        
        logger.info(
            "deliverables_generated",
            session_id=state.session_id,
            decisions_count=len(deliverables.decisions),
            risks_count=len(deliverables.risks),
            faqs_count=len(deliverables.faqs),
            diagrams_count=len(deliverables.diagrams),
            markdown_length=len(deliverables.markdown_report),
        )
        
        # Return state update
        return {
            "deliverables": deliverables,
            "updated_at": deliverables.generated_at,
        }
        
    except Exception as e:
        logger.error(
            "generate_deliverables_node_error",
            session_id=state.session_id,
            error=str(e),
            exc_info=True,
        )
        
        # Add error to state but don't fail the workflow
        # Deliverables generation failure shouldn't block completion
        return {
            "errors": state.errors + [f"Deliverables generation failed: {str(e)}"],
            "warnings": state.warnings + ["Deliverables bundle not available"],
        }

