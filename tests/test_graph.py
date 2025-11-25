"""
Tests for graph/workflow modules.

TODO: Phase 2 - Implement comprehensive workflow tests
"""

import pytest
from datetime import datetime

from app.graph.evaluator import WorkflowEvaluator
from app.graph.state_models import (
    AgentRole,
    ReviewDecision,
    ReviewFeedback,
    WorkflowState,
    WorkflowStatus,
)


def test_workflow_state_creation():
    """Test workflow state initialization."""
    state = WorkflowState(
        session_id="test-session",
        user_request="Test request",
        user_context={"key": "value"}
    )

    assert state.session_id == "test-session"
    assert state.status == WorkflowStatus.PENDING
    assert len(state.messages) == 0
    assert len(state.reviews) == 0


def test_workflow_state_add_message():
    """Test adding messages to workflow state."""
    state = WorkflowState(
        session_id="test-session",
        user_request="Test request"
    )

    state.add_message(
        agent_role=AgentRole.MASTER,
        content="Test message"
    )

    assert len(state.messages) == 1
    assert state.messages[0].agent_role == AgentRole.MASTER
    assert state.messages[0].content == "Test message"


def test_workflow_state_add_review():
    """Test adding reviews to workflow state."""
    state = WorkflowState(
        session_id="test-session",
        user_request="Test request"
    )

    review = ReviewFeedback(
        reviewer_role=AgentRole.REVIEWER_NFR,
        decision=ReviewDecision.APPROVE,
        concerns=[],
        suggestions=[],
        rationale="Looks good"
    )

    state.add_review(review)

    assert len(state.reviews) == 1
    assert state.reviews[0].decision == ReviewDecision.APPROVE


def test_workflow_evaluator_revision():
    """Test workflow evaluator revision logic."""
    state = WorkflowState(
        session_id="test-session",
        user_request="Test request"
    )

    # No reviews yet
    assert WorkflowEvaluator.should_revise(state) is False

    # Add revision request
    review = ReviewFeedback(
        reviewer_role=AgentRole.REVIEWER_SECURITY,
        decision=ReviewDecision.REVISE,
        concerns=["Security issue"],
        suggestions=["Add encryption"],
        rationale="Needs improvement"
    )
    state.add_review(review)

    assert WorkflowEvaluator.should_revise(state) is True


def test_workflow_evaluator_escalation():
    """Test workflow evaluator escalation logic."""
    state = WorkflowState(
        session_id="test-session",
        user_request="Test request"
    )

    # Add critical review
    review = ReviewFeedback(
        reviewer_role=AgentRole.REVIEWER_SECURITY,
        decision=ReviewDecision.ESCALATE,
        concerns=["Critical security flaw"],
        suggestions=[],
        rationale="Requires immediate attention",
        severity="critical"
    )
    state.add_review(review)

    assert WorkflowEvaluator.should_escalate(state) is True


# TODO: Phase 2 - Add more tests:
# - Test workflow graph compilation
# - Test node execution
# - Test conditional routing
# - Test revision loops
# - Test state persistence
# - Integration tests for full workflow

