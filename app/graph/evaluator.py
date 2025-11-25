"""
Workflow evaluator for Agent Council system.

Implements conditional logic for routing workflow based on state.
Determines transitions between nodes in the LangGraph workflow.
"""

from app.graph.state_models import ReviewDecision, WorkflowState
from app.utils.logging import get_logger

logger = get_logger(__name__)


class WorkflowEvaluator:
    """
    Evaluator for workflow transitions.

    Implements conditional edge logic for LangGraph.
    """

    @staticmethod
    def should_revise(state: WorkflowState) -> bool:
        """
        Determine if design needs revision based on reviews.

        Args:
            state: Current workflow state

        Returns:
            True if revision needed, False otherwise
        """
        if not state.reviews:
            return False

        # Check if any reviewer requested revisions
        has_revisions = any(
            r.decision == ReviewDecision.REVISE
            for r in state.reviews
        )

        # Check if we haven't exceeded max revisions
        can_revise = state.can_proceed()

        result = has_revisions and can_revise

        logger.info(
            "revision_evaluation",
            needs_revision=has_revisions,
            can_revise=can_revise,
            result=result,
            revision_count=state.revision_count,
            max_revisions=state.max_revisions
        )

        return result

    @staticmethod
    def should_escalate(state: WorkflowState) -> bool:
        """
        Determine if issue should be escalated to human.

        Args:
            state: Current workflow state

        Returns:
            True if escalation needed, False otherwise
        """
        if not state.reviews:
            return False

        # Check for critical severity issues
        has_critical = any(
            r.severity == "critical"
            for r in state.reviews
        )

        # Check for escalation decisions
        has_escalation = any(
            r.decision == ReviewDecision.ESCALATE
            for r in state.reviews
        )

        # Check if max revisions exceeded
        max_revisions_exceeded = not state.can_proceed()

        result = has_critical or has_escalation or max_revisions_exceeded

        logger.info(
            "escalation_evaluation",
            has_critical=has_critical,
            has_escalation=has_escalation,
            max_revisions_exceeded=max_revisions_exceeded,
            result=result
        )

        return result

    @staticmethod
    def all_reviews_approved(state: WorkflowState) -> bool:
        """
        Check if all reviews approved the design.

        Args:
            state: Current workflow state

        Returns:
            True if all approved, False otherwise
        """
        if not state.reviews:
            return False

        all_approved = all(
            r.decision == ReviewDecision.APPROVE
            for r in state.reviews
        )

        logger.info(
            "approval_evaluation",
            total_reviews=len(state.reviews),
            all_approved=all_approved
        )

        return all_approved

    @staticmethod
    def determine_next_step(state: WorkflowState) -> str:
        """
        Determine the next step in the workflow.

        Args:
            state: Current workflow state

        Returns:
            Next node name
        """
        # If no reviews yet, go to reviewers
        if not state.reviews:
            logger.info("routing_to_reviewers", session_id=state.session_id)
            return "reviewers"

        # Check for escalation conditions
        if WorkflowEvaluator.should_escalate(state):
            logger.info("routing_to_human_approval", session_id=state.session_id)
            return "human_approval"

        # Check if revision needed
        if WorkflowEvaluator.should_revise(state):
            logger.info("routing_to_solution_architect_for_revision", session_id=state.session_id)
            state.increment_revision()
            return "solution_architect"

        # Check if all approved
        if WorkflowEvaluator.all_reviews_approved(state):
            logger.info("routing_to_faq_generation", session_id=state.session_id)
            return "faq_generation"

        # Default: go to human approval for ambiguous cases
        logger.info("routing_to_human_approval_default", session_id=state.session_id)
        return "human_approval"


def create_routing_function():
    """
    Create routing function for LangGraph conditional edges.

    Returns:
        Routing function
    """
    evaluator = WorkflowEvaluator()

    def route(state: WorkflowState) -> str:
        """Route to next node based on state."""
        return evaluator.determine_next_step(state)

    return route

