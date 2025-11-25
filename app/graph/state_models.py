"""
State models for LangGraph workflow.

Defines Pydantic models for workflow state management.
All state must be serializable for LangGraph persistence.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(str, Enum):
    """Agent roles in the council."""
    MASTER = "master"
    SOLUTION_ARCHITECT = "solution_architect"
    REVIEWER_NFR = "reviewer_nfr"
    REVIEWER_SECURITY = "reviewer_security"
    REVIEWER_INTEGRATION = "reviewer_integration"
    REVIEWER_DOMAIN = "reviewer_domain"
    REVIEWER_OPS = "reviewer_ops"
    FAQ = "faq"
    HUMAN = "human"


class ReviewDecision(str, Enum):
    """Review decision outcomes."""
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    ESCALATE = "escalate"


class AgentMessage(BaseModel):
    """
    Message from an agent in the workflow.

    Represents a single agent's contribution to the council discussion.
    """
    agent_role: AgentRole
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewFeedback(BaseModel):
    """
    Feedback from a reviewer agent.

    Contains structured review results with decision and rationale.
    """
    reviewer_role: AgentRole
    decision: ReviewDecision
    concerns: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    rationale: str
    severity: str = Field(default="medium")  # low, medium, high, critical


class DesignDocument(BaseModel):
    """
    Solution architecture design document.

    Represents the evolving design through workflow iterations.
    """
    version: int = Field(default=1)
    title: str
    description: str
    architecture_overview: str = ""
    components: list[dict[str, Any]] = Field(default_factory=list)
    nfr_considerations: dict[str, str] = Field(default_factory=dict)
    security_considerations: dict[str, str] = Field(default_factory=dict)
    integration_points: list[dict[str, Any]] = Field(default_factory=list)
    deployment_notes: str = ""
    diagrams: list[str] = Field(default_factory=list)  # URLs or references
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class WorkflowState(BaseModel):
    """
    Complete state for the Agent Council workflow.

    This is the master state object passed through all LangGraph nodes.
    Must be fully serializable for LangGraph state management.
    """
    # Session management
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)

    # User input
    user_request: str
    user_context: dict[str, Any] = Field(default_factory=dict)

    # Design evolution
    current_design: Optional[DesignDocument] = None
    design_history: list[DesignDocument] = Field(default_factory=list)

    # Agent interactions
    messages: list[AgentMessage] = Field(default_factory=list)
    current_agent: Optional[AgentRole] = None

    # Review cycle
    reviews: list[ReviewFeedback] = Field(default_factory=list)
    revision_count: int = Field(default=0)
    max_revisions: int = Field(default=3)

    # Human approval
    human_approved: bool = False
    human_feedback: Optional[str] = None

    # FAQ and rationale
    faq_entries: list[dict[str, str]] = Field(default_factory=list)
    decision_rationale: str = ""

    # Final output
    final_design: Optional[DesignDocument] = None
    final_summary: str = ""

    # Error handling
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, agent_role: AgentRole, content: str, **metadata) -> None:
        """Add agent message to state."""
        self.messages.append(
            AgentMessage(
                agent_role=agent_role,
                content=content,
                metadata=metadata
            )
        )
        self.updated_at = datetime.utcnow()

    def add_review(self, review: ReviewFeedback) -> None:
        """Add review feedback to state."""
        self.reviews.append(review)
        self.updated_at = datetime.utcnow()

    def needs_revision(self) -> bool:
        """Check if design needs revision based on reviews."""
        if not self.reviews:
            return False
        latest_reviews = self.reviews[-len(AgentRole):] if len(self.reviews) >= len(AgentRole) else self.reviews
        return any(r.decision == ReviewDecision.REVISE for r in latest_reviews)

    def can_proceed(self) -> bool:
        """Check if workflow can proceed (not exceeded max revisions)."""
        return self.revision_count < self.max_revisions

    def increment_revision(self) -> None:
        """Increment revision counter."""
        self.revision_count += 1
        if self.current_design:
            self.design_history.append(self.current_design.model_copy(deep=True))
            self.current_design.version += 1
        self.updated_at = datetime.utcnow()

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

