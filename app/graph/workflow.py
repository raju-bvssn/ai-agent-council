"""
LangGraph workflow definition for Agent Council system.

Defines the workflow graph with nodes, edges, and conditional routing.
"""

from datetime import datetime
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from app.graph.evaluator import WorkflowEvaluator
from app.graph.node_definitions import (
    faq_generation_node,
    finalize_node,
    human_approval_node,
    master_architect_node,
    reviewer_node,
    solution_architect_node,
)
from app.graph.state_models import AgentRole, WorkflowState, WorkflowStatus
from app.state.persistence import get_persistence_manager
from app.utils.exceptions import WorkflowException
from app.utils.logging import get_logger

logger = get_logger(__name__)


def create_workflow_graph() -> StateGraph:
    """
    Create the Agent Council workflow graph.

    Workflow:
    1. Master Architect (initial analysis)
    2. Solution Architect (design document)
    3. Reviewers (parallel evaluation)
    4. Conditional:
       - If revisions needed → Solution Architect (revision loop)
       - If escalation needed → Human Approval
       - If approved → FAQ Generation
    5. Finalize

    Returns:
        Configured StateGraph
    """
    logger.info("creating_workflow_graph")

    # Create graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("master_architect", master_architect_node)
    workflow.add_node("solution_architect", solution_architect_node)

    # Add reviewer nodes
    workflow.add_node(
        "reviewer_nfr",
        lambda state: reviewer_node(state, AgentRole.REVIEWER_NFR)
    )
    workflow.add_node(
        "reviewer_security",
        lambda state: reviewer_node(state, AgentRole.REVIEWER_SECURITY)
    )
    workflow.add_node(
        "reviewer_integration",
        lambda state: reviewer_node(state, AgentRole.REVIEWER_INTEGRATION)
    )

    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("faq_generation", faq_generation_node)
    workflow.add_node("finalize", finalize_node)

    # Set entry point
    workflow.set_entry_point("master_architect")

    # Add edges
    # Master Architect → Solution Architect
    workflow.add_edge("master_architect", "solution_architect")

    # Solution Architect → All Reviewers (parallel)
    workflow.add_edge("solution_architect", "reviewer_nfr")
    workflow.add_edge("solution_architect", "reviewer_security")
    workflow.add_edge("solution_architect", "reviewer_integration")

    # Create a consolidation node for reviewers
    workflow.add_node("consolidate_reviews", _consolidate_reviews_node)
    
    # All reviewers feed into consolidation
    workflow.add_edge("reviewer_nfr", "consolidate_reviews")
    workflow.add_edge("reviewer_security", "consolidate_reviews")
    workflow.add_edge("reviewer_integration", "consolidate_reviews")

    # After review consolidation, determine next step with conditional routing
    def route_after_reviews(state: WorkflowState) -> str:
        """Route after all reviews complete."""
        next_step = WorkflowEvaluator.determine_next_step(state)
        logger.info("routing_decision", next_step=next_step, session_id=state.session_id)
        return next_step

    workflow.add_conditional_edges(
        "consolidate_reviews",
        route_after_reviews,
        {
            "solution_architect": "solution_architect",  # Revision loop
            "human_approval": "human_approval",          # Escalation or approval needed
            "faq_generation": "faq_generation",          # All approved, skip human
        }
    )

    # Human Approval conditional routing
    def route_after_human(state: WorkflowState) -> str:
        """Route after human approval."""
        if state.human_approved:
            return "faq_generation"
        elif state.human_feedback and state.can_proceed():
            return "solution_architect"  # Revision with feedback
        else:
            return "finalize"  # Rejected or max revisions

    workflow.add_conditional_edges(
        "human_approval",
        route_after_human,
        {
            "faq_generation": "faq_generation",
            "solution_architect": "solution_architect",
            "finalize": "finalize",
        }
    )

    # FAQ Generation → Finalize
    workflow.add_edge("faq_generation", "finalize")

    # Finalize → END
    workflow.add_edge("finalize", END)

    logger.info("workflow_graph_created")

    return workflow


def _consolidate_reviews_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Consolidate reviews from all reviewers.
    
    This node doesn't call an agent - it just marks that all reviews are complete
    and updates the workflow state.
    """
    logger.info("consolidating_reviews", session_id=state.session_id, review_count=len(state.reviews))
    
    # Mark as in progress (reviews complete, deciding next step)
    state.status = WorkflowStatus.IN_PROGRESS
    state.updated_at = datetime.utcnow()
    
    return {
        "status": state.status,
        "updated_at": state.updated_at,
    }


def compile_workflow() -> Any:
    """
    Compile the workflow graph.

    Returns:
        Compiled workflow ready for execution
    """
    logger.info("compiling_workflow")

    graph = create_workflow_graph()
    
    # TODO: Phase 2+ - Add LangSmith tracing configuration
    # TODO: Phase 2+ - Add checkpointing for state persistence
    
    compiled = graph.compile()

    logger.info("workflow_compiled")

    return compiled


async def execute_workflow(session_id: str) -> WorkflowState:
    """
    Execute the complete workflow for a session.
    
    Args:
        session_id: Session ID to execute workflow for
        
    Returns:
        Final workflow state
        
    Raises:
        WorkflowException: On execution errors
    """
    try:
        logger.info("workflow_execution_started", session_id=session_id)
        
        # Load session state
        persistence = get_persistence_manager()
        state = persistence.load_state(session_id)
        
        # Mark as in progress
        state.status = WorkflowStatus.IN_PROGRESS
        persistence.save_state(state)
        
        # Compile workflow
        workflow = compile_workflow()
        
        # Execute workflow
        final_state = workflow.invoke(state)
        
        # Convert dict back to WorkflowState if needed
        if isinstance(final_state, dict):
            final_state = WorkflowState(**final_state)
        
        # Save final state
        final_state.status = WorkflowStatus.COMPLETED
        persistence.save_state(final_state)
        
        logger.info("workflow_execution_completed", session_id=session_id)
        
        return final_state
        
    except Exception as e:
        logger.error("workflow_execution_failed", error=str(e), session_id=session_id)
        
        # Update state with error
        try:
            state.status = WorkflowStatus.FAILED
            state.errors.append(str(e))
            persistence.save_state(state)
        except:
            pass
        
        raise WorkflowException(
            f"Workflow execution failed: {str(e)}",
            details={"session_id": session_id}
        )


def execute_workflow_sync(session_id: str) -> WorkflowState:
    """
    Synchronous wrapper for workflow execution.
    
    Args:
        session_id: Session ID to execute workflow for
        
    Returns:
        Final workflow state
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(execute_workflow(session_id))

