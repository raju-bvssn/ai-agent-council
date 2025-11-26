"""
LangGraph node definitions for Agent Council workflow.

Each node represents a step in the workflow and operates on WorkflowState.
Nodes must be pure functions where possible for deterministic behavior.
"""

from typing import Any

from app.agents.factory import AgentFactory
from app.agents.performer import AgentInput
from app.agents.critic import CriticInput
from app.graph.state_models import AgentRole, ReviewDecision, ReviewFeedback, WorkflowState, WorkflowStatus
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _persist_state(state: WorkflowState) -> None:
    """
    Persist workflow state after node execution.
    
    Args:
        state: WorkflowState to persist
    """
    try:
        # Import here to avoid circular dependency
        from app.state.persistence import get_persistence_manager
        
        persistence = get_persistence_manager()
        persistence.save_state(state)
        logger.debug("state_persisted", session_id=state.session_id)
    except Exception as e:
        logger.error("state_persistence_failed", error=str(e), session_id=state.session_id)


def master_architect_node(state: WorkflowState) -> dict[str, Any]:
    """
    Master Architect node - initial requirements analysis.

    Args:
        state: Current workflow state

    Returns:
        State updates
    """
    logger.info("executing_master_architect_node", session_id=state.session_id)

    # Create Master Architect agent
    agent = AgentFactory.create_agent(AgentRole.MASTER)

    # Execute agent
    agent_input = AgentInput(
        request=state.user_request,
        context=state.user_context
    )
    output = agent.run(agent_input)

    # Update state with tool results
    tool_results = output.metadata.get("tool_results", []) if output.metadata else []
    state.add_message(
        agent_role=AgentRole.MASTER,
        content=output.content,
        success=output.success,
        tool_results=tool_results
    )
    state.current_agent = AgentRole.SOLUTION_ARCHITECT
    state.status = WorkflowStatus.IN_PROGRESS

    # Persist state
    _persist_state(state)

    return {
        "messages": state.messages,
        "current_agent": state.current_agent,
        "status": state.status,
        "updated_at": state.updated_at,
    }


def solution_architect_node(state: WorkflowState) -> dict[str, Any]:
    """
    Solution Architect node - creates/updates design document.

    Args:
        state: Current workflow state

    Returns:
        State updates
    """
    logger.info("executing_solution_architect_node", session_id=state.session_id)

    # Create Solution Architect agent
    agent = AgentFactory.create_agent(AgentRole.SOLUTION_ARCHITECT)

    # Build context from previous messages
    context = state.user_context.copy()
    if state.reviews:
        context["reviews"] = [
            {
                "reviewer": r.reviewer_role.value,
                "decision": r.decision.value,
                "concerns": [str(c) for c in r.concerns],
                "suggestions": [str(s) for s in r.suggestions],
            }
            for r in state.reviews
        ]

    # Execute agent
    agent_input = AgentInput(
        request=state.user_request,
        context=context
    )
    output = agent.run(agent_input)

    # Update state with tool results
    tool_results = output.metadata.get("tool_results", []) if output.metadata else []
    state.add_message(
        agent_role=AgentRole.SOLUTION_ARCHITECT,
        content=output.content,
        success=output.success,
        tool_results=tool_results
    )

    # TODO: Phase 2+ - Parse output and update current_design

    # Persist state
    _persist_state(state)

    return {
        "messages": state.messages,
        "updated_at": state.updated_at,
    }


def reviewer_node(state: WorkflowState, reviewer_role: AgentRole) -> dict[str, Any]:
    """
    Generic reviewer node - evaluates design.

    Args:
        state: Current workflow state
        reviewer_role: Role of the reviewer

    Returns:
        State updates
    """
    logger.info("executing_reviewer_node", reviewer=reviewer_role.value, session_id=state.session_id)

    # Create reviewer agent
    agent = AgentFactory.create_agent(reviewer_role)

    # Get latest design/content to review
    content_to_review = state.user_request
    if state.messages:
        # Get latest solution architect message
        sa_messages = [m for m in state.messages if m.agent_role == AgentRole.SOLUTION_ARCHITECT]
        if sa_messages:
            content_to_review = sa_messages[-1].content

    # Execute agent
    critic_input = CriticInput(
        content_to_review=content_to_review,
        context=state.user_context
    )
    output = agent.run(critic_input)

    # Create review feedback
    review = ReviewFeedback(
        reviewer_role=reviewer_role,
        decision=output.decision,
        concerns=output.concerns,
        suggestions=output.suggestions,
        rationale=output.rationale,
        severity=output.severity,
    )

    # Update state with tool results
    tool_results = output.tool_results if hasattr(output, 'tool_results') else []
    state.add_review(review)
    state.add_message(
        agent_role=reviewer_role,
        content=output.rationale,
        success=output.success,
        decision=output.decision.value,
        tool_results=tool_results
    )

    # Persist state
    _persist_state(state)

    return {
        "reviews": state.reviews,
        "messages": state.messages,
        "updated_at": state.updated_at,
    }


def human_approval_node(state: WorkflowState) -> dict[str, Any]:
    """
    Human approval node - pauses for human review.

    Args:
        state: Current workflow state

    Returns:
        State updates
    """
    logger.info("executing_human_approval_node", session_id=state.session_id)

    # Mark as awaiting human approval
    state.status = WorkflowStatus.AWAITING_HUMAN

    # Persist state so UI can display it
    _persist_state(state)

    # TODO: Phase 2+ - Integrate with UI for real-time approval interface

    return {
        "status": state.status,
        "updated_at": state.updated_at,
    }


def faq_generation_node(state: WorkflowState) -> dict[str, Any]:
    """
    FAQ generation node - creates FAQ and rationale.

    Args:
        state: Current workflow state

    Returns:
        State updates
    """
    logger.info("executing_faq_node", session_id=state.session_id)

    # Create FAQ agent
    agent = AgentFactory.create_agent(AgentRole.FAQ)

    # Build context from all messages and reviews
    context = {
        "messages": [
            {"agent": m.agent_role.value, "content": m.content}
            for m in state.messages
        ],
        "reviews": [
            {
                "reviewer": r.reviewer_role.value,
                "decision": r.decision.value,
                "concerns": [str(c) for c in r.concerns],
                "suggestions": [str(s) for s in r.suggestions],
            }
            for r in state.reviews
        ],
    }

    # Execute agent
    agent_input = AgentInput(
        request="Generate FAQ and decision rationale from council discussion",
        context=context
    )
    output = agent.run(agent_input)

    # Update state
    state.add_message(
        agent_role=AgentRole.FAQ,
        content=output.content,
        success=output.success
    )

    # Parse output and update faq_entries and decision_rationale
    if output.success:
        try:
            import json
            faq_data = json.loads(output.content)
            
            # Extract FAQ entries
            if "faq_entries" in faq_data:
                state.faq_entries = faq_data["faq_entries"]
                logger.info("faq_entries_extracted", count=len(state.faq_entries))
            
            # Extract decision rationale
            if "decision_rationale" in faq_data:
                state.decision_rationale = faq_data["decision_rationale"]
                logger.info("decision_rationale_extracted")
            
            # Extract key takeaways if present
            if "key_takeaways" in faq_data:
                state.metadata["key_takeaways"] = faq_data["key_takeaways"]
                
        except json.JSONDecodeError as e:
            logger.warning("faq_json_parse_failed", error=str(e))
            # Fallback: treat entire content as rationale
            state.decision_rationale = output.content
    
    # Persist state
    _persist_state(state)

    return {
        "messages": state.messages,
        "faq_entries": state.faq_entries,
        "decision_rationale": state.decision_rationale,
        "metadata": state.metadata,
        "updated_at": state.updated_at,
    }


def finalize_node(state: WorkflowState) -> dict[str, Any]:
    """
    Finalize node - completes the workflow.

    Args:
        state: Current workflow state

    Returns:
        State updates
    """
    logger.info("executing_finalize_node", session_id=state.session_id)

    # Copy current design to final design
    if state.current_design:
        state.final_design = state.current_design.model_copy(deep=True)
        logger.info("final_design_set", version=state.final_design.version)

    # Generate final summary
    summary_parts = [
        f"Agent Council Session completed for: {state.user_request}",
        f"Total messages: {len(state.messages)}",
        f"Total reviews: {len(state.reviews)}",
        f"Revisions: {state.revision_count}",
    ]
    
    if state.human_approved:
        summary_parts.append("Human approval: ✅ Approved")
    
    state.final_summary = "\n".join(summary_parts)

    # Mark as completed
    state.status = WorkflowStatus.COMPLETED

    # TODO: Phase 3 - Export diagrams (Lucid AI integration)
    # TODO: Phase 3 - Create deliverables (PDF, Markdown)

    # Persist final state
    _persist_state(state)

    return {
        "status": state.status,
        "final_design": state.final_design,
        "final_summary": state.final_summary,
        "updated_at": state.updated_at,
    }


# Node function mapping for easy access
NODE_FUNCTIONS = {
    "master_architect": master_architect_node,
    "solution_architect": solution_architect_node,
    "human_approval": human_approval_node,
    "faq_generation": faq_generation_node,
    "finalize": finalize_node,
}

