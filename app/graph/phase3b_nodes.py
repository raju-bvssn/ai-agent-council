"""
Phase 3B node definitions for Agent Council workflow.

New nodes for multi-agent debate, consensus, and adjudication.
"""

import asyncio
from typing import Any, Dict

from app.agents.factory import AgentFactory
from app.agents.performer import AgentInput
from app.graph.debate import detect_disagreements, run_debates_parallel, compute_consensus
from app.graph.state_models import (
    AgentRole,
    ReviewerRoundResult,
    WorkflowState,
    WorkflowStatus
)
from app.state.persistence import get_persistence_manager
from app.utils.logging import get_logger

logger = get_logger(__name__)


def detect_disagreements_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Detect disagreements between reviewer agents.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates with detected disagreements
    """
    logger.info("executing_detect_disagreements_node", session_id=state.session_id)
    
    # Get latest reviews
    if not state.reviews:
        logger.warning("no_reviews_for_disagreement_detection", session_id=state.session_id)
        return {}
    
    # Detect disagreements
    disagreements = detect_disagreements(state.reviews)
    
    # Update state
    if state.reviewer_rounds:
        # Add to latest round
        state.reviewer_rounds[-1].disagreements = disagreements
    
    logger.info(
        "disagreements_detected",
        session_id=state.session_id,
        count=len(disagreements)
    )
    
    # Persist state
    _persist_state(state)
    
    return {
        "reviewer_rounds": state.reviewer_rounds,
        "updated_at": state.updated_at
    }


def debate_cycle_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Facilitate debates for unresolved disagreements.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates with debate outcomes
    """
    logger.info("executing_debate_cycle_node", session_id=state.session_id)
    
    # Get disagreements from latest round
    if not state.reviewer_rounds or not state.reviewer_rounds[-1].disagreements:
        logger.warning("no_disagreements_for_debate", session_id=state.session_id)
        return {}
    
    disagreements = state.reviewer_rounds[-1].disagreements
    
    # Get context (current design)
    context = state.user_request
    if state.messages:
        # Get latest solution architect message
        sa_messages = [m for m in state.messages if m.agent_role == AgentRole.SOLUTION_ARCHITECT]
        if sa_messages:
            context += "\n\n" + sa_messages[-1].content
    
    # Run debates in parallel
    debate_outcomes = asyncio.run(run_debates_parallel(
        disagreements=disagreements,
        context=context,
        model=state.selected_model,  # Use selected model or auto-select
        max_rounds=2
    ))
    
    # Update state
    state.debates.extend(debate_outcomes)
    if state.reviewer_rounds:
        state.reviewer_rounds[-1].debates = debate_outcomes
    
    logger.info(
        "debates_completed",
        session_id=state.session_id,
        total_debates=len(debate_outcomes),
        consensus_reached=sum(1 for d in debate_outcomes if d.consensus_reached)
    )
    
    # Persist state
    _persist_state(state)
    
    return {
        "debates": state.debates,
        "reviewer_rounds": state.reviewer_rounds,
        "updated_at": state.updated_at
    }


def compute_consensus_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Compute consensus from reviews and debates.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates with consensus result
    """
    logger.info("executing_compute_consensus_node", session_id=state.session_id)
    
    # Get latest reviews and debates
    reviews = state.reviews
    debates = state.debates
    
    if not reviews:
        logger.warning("no_reviews_for_consensus", session_id=state.session_id)
        return {}
    
    # Compute consensus
    consensus_result = compute_consensus(
        reviews=reviews,
        debates=debates,
        threshold=0.65
    )
    
    # Update state
    state.consensus_history.append(consensus_result)
    if state.reviewer_rounds:
        state.reviewer_rounds[-1].consensus = consensus_result
        state.reviewer_rounds[-1].requires_adjudication = not consensus_result.agreed
    
    state.requires_adjudication = not consensus_result.agreed
    
    logger.info(
        "consensus_computed",
        session_id=state.session_id,
        agreed=consensus_result.agreed,
        confidence=consensus_result.confidence,
        requires_adjudication=state.requires_adjudication
    )
    
    # Persist state
    _persist_state(state)
    
    return {
        "consensus_history": state.consensus_history,
        "reviewer_rounds": state.reviewer_rounds,
        "requires_adjudication": state.requires_adjudication,
        "updated_at": state.updated_at
    }


def architect_adjudicator_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Architect Adjudicator makes final decisions on unresolved conflicts.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates with adjudication results
    """
    logger.info("executing_architect_adjudicator_node", session_id=state.session_id)
    
    # Create Architect Adjudicator agent
    agent = AgentFactory.create_agent(AgentRole.ARCHITECT_ADJUDICATOR)
    
    # Get latest consensus
    latest_consensus = state.consensus_history[-1] if state.consensus_history else None
    
    # Get unresolved disagreements
    unresolved_disagreements = []
    if state.reviewer_rounds and state.reviewer_rounds[-1].debates:
        unresolved_disagreements = [
            d.disagreement for d in state.reviewer_rounds[-1].debates
            if not d.consensus_reached
        ]
    
    # Build context
    context = {
        "reviews": [r.dict() for r in state.reviews],
        "debates": [d.dict() for d in state.debates],
        "consensus": latest_consensus.dict() if latest_consensus else {},
        "unresolved_disagreements": [d.dict() for d in unresolved_disagreements],
        "current_design": state.messages[-1].content if state.messages else state.user_request
    }
    
    # Execute agent
    agent_input = AgentInput(
        request=state.user_request,
        context=context
    )
    output = agent.run(agent_input)
    
    # Parse output
    import json
    try:
        adjudication = json.loads(output.content)
    except json.JSONDecodeError:
        adjudication = {"architecture_rationale": output.content}
    
    # Update state
    state.final_architecture_rationale = adjudication.get("architecture_rationale", "")
    state.adjudication_complete = True
    
    # Add FAQ entries
    faq_entries = adjudication.get("faq_entries", [])
    state.faq_entries.extend(faq_entries)
    
    # Add message
    tool_results = output.metadata.get("tool_results", []) if output.metadata else []
    state.add_message(
        agent_role=AgentRole.ARCHITECT_ADJUDICATOR,
        content=output.content,
        success=output.success,
        tool_results=tool_results
    )
    
    logger.info(
        "architect_adjudicator_completed",
        session_id=state.session_id,
        decisions=len(adjudication.get("final_decisions", [])),
        faq_entries=len(faq_entries)
    )
    
    # Persist state
    _persist_state(state)
    
    return {
        "final_architecture_rationale": state.final_architecture_rationale,
        "adjudication_complete": state.adjudication_complete,
        "faq_entries": state.faq_entries,
        "messages": state.messages,
        "updated_at": state.updated_at
    }


def create_reviewer_round_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Create a new reviewer round after consolidating reviews.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates with new reviewer round
    """
    logger.info("executing_create_reviewer_round_node", session_id=state.session_id)
    
    # Create new round
    round_number = len(state.reviewer_rounds) + 1
    
    reviewer_round = ReviewerRoundResult(
        round_number=round_number,
        reviews=list(state.reviews),  # Copy current reviews
        disagreements=[],
        debates=[],
        consensus=None,
        requires_adjudication=False
    )
    
    state.reviewer_rounds.append(reviewer_round)
    state.current_round = round_number
    
    logger.info(
        "reviewer_round_created",
        session_id=state.session_id,
        round_number=round_number
    )
    
    # Persist state
    _persist_state(state)
    
    return {
        "reviewer_rounds": state.reviewer_rounds,
        "current_round": state.current_round,
        "updated_at": state.updated_at
    }


def _persist_state(state: WorkflowState) -> None:
    """Persist workflow state after node execution."""
    try:
        persistence = get_persistence_manager()
        persistence.save_state(state)
        logger.debug("state_persisted", session_id=state.session_id)
    except Exception as e:
        logger.error("state_persistence_failed", error=str(e), session_id=state.session_id)

