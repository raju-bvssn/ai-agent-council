"""
LangGraph workflow definition for Agent Council system.

Defines the workflow graph with nodes, edges, and conditional routing.
"""

from datetime import datetime
from typing import Any, Dict, Optional

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
from app.graph.phase3b_nodes import (
    architect_adjudicator_node,
    compute_consensus_node,
    create_reviewer_round_node,
    debate_cycle_node,
    detect_disagreements_node,
)
from app.graph.phase3c_nodes import (
    generate_deliverables_node,
)
from app.graph.state_models import (
    AgentRole,
    HumanAction,
    WorkflowResult,
    WorkflowState,
    WorkflowStatus,
)
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
    workflow.add_node("generate_deliverables", generate_deliverables_node)  # Phase 3C
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
    
    # Phase 3B: Add debate and consensus nodes
    workflow.add_node("create_reviewer_round", create_reviewer_round_node)
    workflow.add_node("detect_disagreements", detect_disagreements_node)
    workflow.add_node("debate_cycle", debate_cycle_node)
    workflow.add_node("compute_consensus", compute_consensus_node)
    workflow.add_node("architect_adjudicator", architect_adjudicator_node)
    
    # Consolidate reviews → Create reviewer round
    workflow.add_edge("consolidate_reviews", "create_reviewer_round")
    
    # Create reviewer round → Detect disagreements
    workflow.add_edge("create_reviewer_round", "detect_disagreements")
    
    # Detect disagreements → Conditional: debate or consensus
    def route_after_disagreements(state: WorkflowState) -> str:
        """Route after disagreement detection."""
        if state.reviewer_rounds and state.reviewer_rounds[-1].disagreements:
            logger.info("disagreements_found_routing_to_debate", session_id=state.session_id)
            return "debate_cycle"
        else:
            logger.info("no_disagreements_routing_to_consensus", session_id=state.session_id)
            return "compute_consensus"
    
    workflow.add_conditional_edges(
        "detect_disagreements",
        route_after_disagreements,
        {
            "debate_cycle": "debate_cycle",
            "compute_consensus": "compute_consensus",
        }
    )
    
    # Debate cycle → Compute consensus
    workflow.add_edge("debate_cycle", "compute_consensus")
    
    # Compute consensus → Conditional: adjudication or proceed
    def route_after_consensus(state: WorkflowState) -> str:
        """Route after consensus computation."""
        if state.requires_adjudication:
            logger.info("consensus_not_reached_routing_to_adjudicator", session_id=state.session_id)
            return "architect_adjudicator"
        else:
            logger.info("consensus_reached_routing_to_next", session_id=state.session_id)
            return "evaluate_next_step"
    
    workflow.add_conditional_edges(
        "compute_consensus",
        route_after_consensus,
        {
            "architect_adjudicator": "architect_adjudicator",
            "evaluate_next_step": "evaluate_next_step",
        }
    )
    
    # Architect adjudicator → Evaluate next step
    workflow.add_edge("architect_adjudicator", "evaluate_next_step")
    
    # Evaluate next step node (replaces old route_after_reviews)
    workflow.add_node("evaluate_next_step", _evaluate_next_step_node)
    
    # After evaluation, determine next step with conditional routing
    def route_after_evaluation(state: WorkflowState) -> str:
        """Route after evaluation of consensus/adjudication."""
        next_step = WorkflowEvaluator.determine_next_step(state)
        logger.info("routing_decision", next_step=next_step, session_id=state.session_id)
        return next_step

    workflow.add_conditional_edges(
        "evaluate_next_step",
        route_after_evaluation,
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

    # FAQ Generation → Generate Deliverables (Phase 3C)
    workflow.add_edge("faq_generation", "generate_deliverables")
    
    # Generate Deliverables → Finalize (Phase 3C)
    workflow.add_edge("generate_deliverables", "finalize")

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


def _evaluate_next_step_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Evaluate next step after consensus/adjudication.
    
    This node prepares the state for conditional routing based on
    the outcome of the review/debate/consensus cycle.
    """
    logger.info(
        "evaluating_next_step",
        session_id=state.session_id,
        consensus_reached=not state.requires_adjudication,
        adjudication_complete=state.adjudication_complete
    )
    
    # Update state
    state.status = WorkflowStatus.IN_PROGRESS
    state.updated_at = datetime.utcnow()
    
    # Persist state
    try:
        from app.state.persistence import get_persistence_manager
        persistence = get_persistence_manager()
        persistence.save_state(state)
    except Exception as e:
        logger.error("state_persistence_failed", error=str(e), session_id=state.session_id)
    
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
        from app.state.persistence import get_persistence_manager
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


def run_council_workflow(session_id: str) -> WorkflowResult:
    """
    Start council workflow execution.
    
    Executes workflow until:
    - AWAITING_HUMAN status (pauses for approval)
    - COMPLETED status (workflow finished)
    - FAILED status (error occurred)
    
    Args:
        session_id: Session ID to execute
        
    Returns:
        WorkflowResult with current status
        
    Raises:
        WorkflowException: On execution errors
    """
    try:
        logger.info("run_council_workflow_started", session_id=session_id)
        
        # Load session state
        from app.state.persistence import get_persistence_manager
        persistence = get_persistence_manager()
        state = persistence.load_state(session_id)
        
        # Capture LangSmith run_id for tracing (POC)
        from app.observability import get_current_run_id, get_trace_url, is_tracing_enabled
        if is_tracing_enabled():
            run_id = get_current_run_id()
            if run_id:
                state.langsmith_run_id = run_id
                state.langsmith_trace_url = get_trace_url(run_id)
                logger.info("langsmith_trace_captured", run_id=run_id, session_id=session_id)
        
        # Validate not already running
        if state.status == WorkflowStatus.IN_PROGRESS:
            logger.warning("workflow_already_running", session_id=session_id)
            return WorkflowResult.from_workflow_state(state)
        
        # Mark as in progress
        state.status = WorkflowStatus.IN_PROGRESS
        state.updated_at = datetime.utcnow()
        persistence.save_state(state)
        
        # Execute workflow in a background thread to avoid blocking
        import threading
        
        def execute_async():
            try:
                # Compile and execute workflow
                workflow = compile_workflow()
                
                # Convert state to dict for LangGraph
                state_dict = state.model_dump()
                
                # Execute workflow
                result = workflow.invoke(state_dict)
                
                # Convert result back to WorkflowState
                if isinstance(result, dict):
                    updated_state = WorkflowState(**result)
                else:
                    updated_state = result
                
                # Save updated state
                persistence.save_state(updated_state)
                
                logger.info("workflow_execution_completed_async", 
                           session_id=session_id,
                           status=updated_state.status.value)
                
            except Exception as e:
                logger.error("workflow_execution_failed_async", 
                            error=str(e), 
                            session_id=session_id)
                
                # Update state with error
                try:
                    error_state = persistence.load_state(session_id)
                    error_state.status = WorkflowStatus.FAILED
                    error_state.errors.append(str(e))
                    persistence.save_state(error_state)
                except:
                    pass
        
        # Start execution in background
        thread = threading.Thread(target=execute_async, daemon=True)
        thread.start()
        
        # Return current state immediately (will show IN_PROGRESS)
        logger.info("run_council_workflow_initiated", session_id=session_id)
        
        return WorkflowResult.from_workflow_state(state, current_node="master_architect")
        
    except Exception as e:
        logger.error("run_council_workflow_failed", error=str(e), session_id=session_id)
        raise WorkflowException(
            f"Failed to start workflow: {str(e)}",
            details={"session_id": session_id}
        )


def step_council_workflow(session_id: str, action: HumanAction, feedback: Optional[str] = None) -> WorkflowResult:
    """
    Resume workflow execution after human action.
    
    Args:
        session_id: Session ID to resume
        action: Human action (APPROVE, REVISE, REJECT)
        feedback: Optional feedback/comments from human
        
    Returns:
        WorkflowResult with updated status
        
    Raises:
        WorkflowException: On execution errors
    """
    try:
        logger.info("step_council_workflow_started", 
                   session_id=session_id, 
                   action=action.value)
        
        # Load current state
        from app.state.persistence import get_persistence_manager
        persistence = get_persistence_manager()
        state = persistence.load_state(session_id)
        
        # Validate in correct state
        if state.status != WorkflowStatus.AWAITING_HUMAN:
            raise WorkflowException(
                f"Cannot step workflow: status is {state.status.value}, expected awaiting_human",
                details={"session_id": session_id, "status": state.status.value}
            )
        
        # Process human action
        if action == HumanAction.APPROVE:
            state.human_approved = True
            state.human_feedback = feedback
            logger.info("human_approved_design", session_id=session_id)
            
        elif action == HumanAction.REVISE:
            state.human_approved = False
            state.human_feedback = feedback or "Please revise the design based on reviewer feedback."
            state.increment_revision()
            logger.info("human_requested_revision", session_id=session_id, revision=state.revision_count)
            
        elif action == HumanAction.REJECT:
            state.human_approved = False
            state.human_feedback = feedback
            state.status = WorkflowStatus.CANCELLED
            persistence.save_state(state)
            logger.info("human_rejected_design", session_id=session_id)
            return WorkflowResult.from_workflow_state(state, current_node="finalize")
        
        # Mark as in progress and continue workflow
        state.status = WorkflowStatus.IN_PROGRESS
        state.updated_at = datetime.utcnow()
        persistence.save_state(state)
        
        # Continue execution in background
        import threading
        
        def continue_execution():
            try:
                # The workflow should continue from after human_approval node
                # For now, we'll re-execute with the updated state
                workflow = compile_workflow()
                
                # Convert to dict
                state_dict = state.model_dump()
                
                # Execute from current position
                # Note: In a full implementation, we'd use LangGraph checkpointing
                # For Phase 2C, we'll restart from solution_architect if revise,
                # or faq_generation if approved
                
                if state.human_approved:
                    # Skip to FAQ generation
                    from app.graph.node_definitions import faq_generation_node, finalize_node
                    
                    # Execute FAQ generation
                    faq_result = faq_generation_node(state)
                    state = WorkflowState(**{**state.model_dump(), **faq_result})
                    
                    # Finalize
                    final_result = finalize_node(state)
                    state = WorkflowState(**{**state.model_dump(), **final_result})
                    
                    state.status = WorkflowStatus.COMPLETED
                    
                else:
                    # Revision requested - go through solution architect again
                    from app.graph.node_definitions import solution_architect_node, reviewer_node
                    
                    # Solution architect revises
                    sa_result = solution_architect_node(state)
                    state = WorkflowState(**{**state.model_dump(), **sa_result})
                    
                    # Run reviewers again
                    for role in [AgentRole.REVIEWER_NFR, AgentRole.REVIEWER_SECURITY, AgentRole.REVIEWER_INTEGRATION]:
                        review_result = reviewer_node(state, role)
                        state = WorkflowState(**{**state.model_dump(), **review_result})
                    
                    # Determine next step
                    next_step = WorkflowEvaluator.determine_next_step(state)
                    
                    if next_step == "human_approval" or state.revision_count >= state.max_revisions:
                        state.status = WorkflowStatus.AWAITING_HUMAN
                    elif next_step == "faq_generation":
                        # All approved, continue to FAQ
                        from app.graph.node_definitions import faq_generation_node, finalize_node
                        
                        faq_result = faq_generation_node(state)
                        state = WorkflowState(**{**state.model_dump(), **faq_result})
                        
                        final_result = finalize_node(state)
                        state = WorkflowState(**{**state.model_dump(), **final_result})
                        
                        state.status = WorkflowStatus.COMPLETED
                
                # Save final state
                persistence.save_state(state)
                
                logger.info("workflow_step_completed", 
                           session_id=session_id,
                           status=state.status.value)
                
            except Exception as e:
                logger.error("workflow_step_failed", error=str(e), session_id=session_id)
                try:
                    error_state = persistence.load_state(session_id)
                    error_state.status = WorkflowStatus.FAILED
                    error_state.errors.append(str(e))
                    persistence.save_state(error_state)
                except:
                    pass
        
        # Start continuation in background
        thread = threading.Thread(target=continue_execution, daemon=True)
        thread.start()
        
        logger.info("step_council_workflow_initiated", session_id=session_id)
        
        return WorkflowResult.from_workflow_state(state, current_node="resuming")
        
    except WorkflowException:
        raise
    except Exception as e:
        logger.error("step_council_workflow_failed", error=str(e), session_id=session_id)
        raise WorkflowException(
            f"Failed to step workflow: {str(e)}",
            details={"session_id": session_id}
        )


def get_workflow_status(session_id: str) -> WorkflowResult:
    """
    Get current workflow status.
    
    Args:
        session_id: Session ID to check
        
    Returns:
        WorkflowResult with current status
        
    Raises:
        WorkflowException: If session not found
    """
    try:
        from app.state.persistence import get_persistence_manager
        persistence = get_persistence_manager()
        state = persistence.load_state(session_id)
        
        return WorkflowResult.from_workflow_state(state)
        
    except Exception as e:
        logger.error("get_workflow_status_failed", error=str(e), session_id=session_id)
        raise WorkflowException(
            f"Failed to get workflow status: {str(e)}",
            details={"session_id": session_id}
        )

