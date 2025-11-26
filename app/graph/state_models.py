"""
State models for LangGraph workflow.

Defines Pydantic models for workflow state management.
All state must be serializable for LangGraph persistence.
"""

import operator
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union, Annotated

from pydantic import BaseModel, Field


class Concern(BaseModel):
    """Structured concern from a critic/reviewer agent."""
    area: str
    description: str
    severity: str = "medium"


class Suggestion(BaseModel):
    """Structured suggestion from a critic/reviewer agent."""
    area: str
    suggestion: str
    priority: Optional[str] = None


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
    ARCHITECT_ADJUDICATOR = "architect_adjudicator"  # Phase 3B: Conflict resolver
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
    tool_results: list[dict[str, Any]] = Field(default_factory=list)  # Results from tool invocations


class ReviewFeedback(BaseModel):
    """
    Feedback from a reviewer agent.

    Contains structured review results with decision and rationale.
    Supports both simple strings and structured Concern/Suggestion objects.
    """
    reviewer_role: AgentRole
    decision: ReviewDecision
    concerns: list[Union[str, Concern]] = Field(default_factory=list)
    suggestions: list[Union[str, Suggestion]] = Field(default_factory=list)
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


class Disagreement(BaseModel):
    """
    Represents a disagreement between reviewer agents.
    
    Captures conflicting recommendations that require resolution
    through debate or adjudication.
    """
    disagreement_id: str
    agent_roles: list[AgentRole]  # Agents involved in disagreement
    topic: str  # What they disagree about
    positions: dict[str, str]  # agent_role -> their position
    severity: str = "medium"  # low, medium, high, critical
    category: str  # e.g., "integration_pattern", "security_approach", "performance_tradeoff"
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class DebateOutcome(BaseModel):
    """
    Result of a debate cycle between disagreeing agents.
    
    Contains the debate process, revised positions, and whether
    consensus was reached.
    """
    debate_id: str
    disagreement: Disagreement
    debate_rounds: int
    agent_positions_revised: dict[str, str]  # agent_role -> revised position
    consensus_reached: bool
    resolution_summary: str
    confidence: float  # 0-1, how confident the resolution is
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConsensusResult(BaseModel):
    """
    Result of consensus computation across all reviewer feedback.
    
    Uses weighted scoring to determine if agents agree on the design.
    """
    round_id: str
    agreed: bool  # Overall consensus reached
    confidence: float  # Weighted confidence score (0-1)
    summary: str  # Summary of consensus or remaining issues
    disagreements_resolved: list[str]  # IDs of resolved disagreements
    disagreements_unresolved: list[str]  # IDs still requiring adjudication
    vote_breakdown: dict[str, str]  # agent_role -> vote (approve/revise/reject)
    weights_applied: dict[str, float]  # agent_role -> weight used
    threshold: float = 0.65  # Minimum confidence for consensus
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReviewerRoundResult(BaseModel):
    """
    Complete result of a reviewer round including parallel execution,
    debates, and consensus.
    """
    round_number: int
    reviews: list[ReviewFeedback]
    disagreements: list[Disagreement] = Field(default_factory=list)
    debates: list[DebateOutcome] = Field(default_factory=list)
    consensus: Optional[ConsensusResult] = None
    requires_adjudication: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Phase 3C: Deliverables Models
# ============================================================================

class ArchitectureSummary(BaseModel):
    """
    High-level architecture summary for deliverables.
    
    Provides executive overview of the proposed solution with key capabilities
    and non-functional highlights.
    """
    overview: str
    key_capabilities: list[str] = Field(default_factory=list)
    non_functional_highlights: list[str] = Field(default_factory=list)


class DecisionRecord(BaseModel):
    """
    Architecture Decision Record (ADR-style) for key design decisions.
    
    Documents critical decisions made during the architecture review process
    with full context and rationale.
    """
    id: str
    title: str
    context: str
    decision: str
    rationale: str
    consequences: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RiskItem(BaseModel):
    """
    Technical risk item with impact assessment and mitigation strategy.
    
    Identifies potential risks in the proposed architecture with recommended
    mitigations for the implementation team.
    """
    id: str
    description: str
    impact: str  # low, medium, high, critical
    likelihood: str  # low, medium, high
    mitigation: str
    owner: Optional[str] = None  # Suggested owner or team
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FAQItem(BaseModel):
    """
    FAQ entry for human architect review board.
    
    Captures common questions and answers derived from the agent council
    discussions, debates, and final decisions.
    """
    question: str
    answer: str
    source: Optional[str] = None  # e.g., "debate_outcome", "adjudicator", "reviewer"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DiagramDescriptor(BaseModel):
    """
    Diagram descriptor with Lucid URL or Mermaid fallback.
    
    Describes architecture diagrams generated or recommended by the system.
    Supports both external diagramming tools (Lucid) and embedded Mermaid.
    """
    diagram_type: str  # "context", "integration_flow", "deployment", "sequence"
    title: str
    description: str
    lucid_url: Optional[str] = None  # External Lucid diagram link
    mermaid_source: Optional[str] = None  # Embedded Mermaid diagram source
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeliverablesBundle(BaseModel):
    """
    Complete deliverables bundle for customer presentation.
    
    Aggregates all architecture artifacts, decisions, risks, and documentation
    into a single comprehensive package suitable for client delivery.
    """
    session_id: str
    architecture_summary: ArchitectureSummary
    decisions: list[DecisionRecord] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    faqs: list[FAQItem] = Field(default_factory=list)
    diagrams: list[DiagramDescriptor] = Field(default_factory=list)
    markdown_report: str = ""  # Complete Markdown-formatted report
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    workflow_version: str = "3.0"  # Phase 3C
    includes_tool_insights: bool = False  # Whether external tools were used
    demo_mode: bool = False  # Whether generated in demo mode


class WorkflowState(BaseModel):
    """
    Complete state for the Agent Council workflow.

    This is the master state object passed through all LangGraph nodes.
    Must be fully serializable for LangGraph state management.
    """
    # Session management
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Annotated[datetime, lambda x, y: max(x, y) if x and y else x or y] = Field(default_factory=datetime.utcnow)
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)

    # User input
    user_request: str
    user_context: dict[str, Any] = Field(default_factory=dict)

    # Design evolution
    current_design: Optional[DesignDocument] = None
    design_history: list[DesignDocument] = Field(default_factory=list)

    # Agent interactions
    messages: Annotated[list[AgentMessage], operator.add] = Field(default_factory=list)
    current_agent: Optional[AgentRole] = None

    # Review cycle
    reviews: Annotated[list[ReviewFeedback], operator.add] = Field(default_factory=list)
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
    final_architecture_rationale: Optional[str] = None  # From Architect Adjudicator

    # Phase 3B: Model selection
    selected_model: Optional[str] = None  # Manual override model
    auto_model: bool = True  # Whether to use auto-selection
    models_used: dict[str, str] = Field(default_factory=dict)  # agent_role -> model_used

    # Phase 3B: Multi-agent debate and consensus
    reviewer_rounds: Annotated[list[ReviewerRoundResult], operator.add] = Field(default_factory=list)
    current_round: int = 0
    debates: Annotated[list[DebateOutcome], operator.add] = Field(default_factory=list)
    consensus_history: Annotated[list[ConsensusResult], operator.add] = Field(default_factory=list)
    requires_adjudication: bool = False
    adjudication_complete: bool = False

    # Error handling
    errors: Annotated[list[str], operator.add] = Field(default_factory=list)
    warnings: Annotated[list[str], operator.add] = Field(default_factory=list)

    # Phase 3C: Deliverables
    deliverables: Optional[DeliverablesBundle] = None

    # LangSmith tracing
    langsmith_run_id: Optional[str] = None
    langsmith_trace_url: Optional[str] = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, agent_role: AgentRole, content: str, tool_results: Optional[list] = None, **metadata) -> None:
        """Add agent message to state with optional tool results."""
        self.messages.append(
            AgentMessage(
                agent_role=agent_role,
                content=content,
                metadata=metadata,
                tool_results=tool_results or []
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


class HumanAction(str, Enum):
    """Human actions in workflow."""
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"


class WorkflowResult(BaseModel):
    """
    Workflow execution result for API responses.
    
    Lightweight model for returning workflow status to clients.
    """
    session_id: str
    status: WorkflowStatus
    current_node: Optional[str] = None
    current_agent: Optional[AgentRole] = None
    
    # Timeline and progress
    messages: list[AgentMessage] = Field(default_factory=list)
    reviews: list[ReviewFeedback] = Field(default_factory=list)
    
    # Current design
    design: Optional[DesignDocument] = None
    
    # FAQ and rationale
    faq_entries: list[dict[str, str]] = Field(default_factory=list)
    decision_rationale: str = ""
    final_architecture_rationale: Optional[str] = None
    
    # Metadata
    revision_count: int = 0
    max_revisions: int = 3
    human_approved: bool = False
    
    # LangSmith tracing (POC)
    langsmith_run_id: Optional[str] = None
    langsmith_trace_url: Optional[str] = None
    
    # Phase 3B: Model selection
    selected_model: Optional[str] = None
    auto_model: bool = True
    models_used: dict[str, str] = Field(default_factory=dict)
    
    # Phase 3B: Debate and consensus
    current_round: int = 0
    total_disagreements: int = 0
    total_debates: int = 0
    debates_resolved: int = 0
    consensus_confidence: Optional[float] = None
    consensus_summary: Optional[str] = None
    requires_adjudication: bool = False
    adjudication_complete: bool = False
    
    # Error handling
    error: Optional[str] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    
    # LangSmith tracing (POC)
    langsmith_run_id: Optional[str] = None
    langsmith_trace_url: Optional[str] = None
    
    # Phase 3C: Deliverables
    deliverables: Optional[DeliverablesBundle] = None
    
    @classmethod
    def from_workflow_state(cls, state: WorkflowState, current_node: Optional[str] = None) -> "WorkflowResult":
        """
        Create WorkflowResult from WorkflowState.
        
        Args:
            state: Complete workflow state
            current_node: Current node name (if known)
            
        Returns:
            WorkflowResult for API response
        """
        # Compute Phase 3B statistics
        total_disagreements = sum(len(r.disagreements) for r in state.reviewer_rounds)
        total_debates = len(state.debates)
        debates_resolved = sum(1 for d in state.debates if d.consensus_reached)
        
        # Get latest consensus
        consensus_confidence = None
        consensus_summary = None
        if state.consensus_history:
            latest = state.consensus_history[-1]
            consensus_confidence = latest.confidence
            consensus_summary = latest.summary
        
        return cls(
            session_id=state.session_id,
            status=state.status,
            current_node=current_node,
            current_agent=state.current_agent,
            messages=state.messages,
            reviews=state.reviews,
            design=state.current_design,
            faq_entries=state.faq_entries,
            decision_rationale=state.decision_rationale,
            final_architecture_rationale=state.final_architecture_rationale,
            revision_count=state.revision_count,
            max_revisions=state.max_revisions,
            human_approved=state.human_approved,
            # Phase 3B fields
            selected_model=state.selected_model,
            auto_model=state.auto_model,
            models_used=state.models_used,
            current_round=state.current_round,
            total_disagreements=total_disagreements,
            total_debates=total_debates,
            debates_resolved=debates_resolved,
            consensus_confidence=consensus_confidence,
            consensus_summary=consensus_summary,
            requires_adjudication=state.requires_adjudication,
            adjudication_complete=state.adjudication_complete,
            # Error handling
            error=state.errors[-1] if state.errors else None,
            errors=state.errors,
            warnings=state.warnings,
            # LangSmith tracing (POC)
            langsmith_run_id=state.langsmith_run_id,
            langsmith_trace_url=state.langsmith_trace_url,
            # Phase 3C: Deliverables
            deliverables=state.deliverables,
        )
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

