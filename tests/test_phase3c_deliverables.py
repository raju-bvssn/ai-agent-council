"""
Tests for Phase 3C - Deliverables Engine.

Tests the generation of architecture deliverables including summaries,
decision records, risks, FAQs, and diagrams.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app.graph.state_models import (
    WorkflowState,
    WorkflowStatus,
    AgentRole,
    ReviewFeedback,
    ReviewDecision,
    DesignDocument,
    Disagreement,
    DebateOutcome,
    ConsensusResult,
    ReviewerRoundResult,
)
from app.graph.deliverables.service import (
    build_architecture_summary,
    build_decision_records,
    build_risks_and_mitigations,
    build_faq_items,
    build_diagram_descriptors,
    assemble_markdown_report,
    build_deliverables_bundle,
)


@pytest.fixture
def sample_workflow_state():
    """Create a sample completed workflow state for testing."""
    state = WorkflowState(
        session_id="test-session-123",
        user_request="Design a secure customer portal integration with Salesforce",
        status=WorkflowStatus.COMPLETED,
    )
    
    # Add a design document
    state.current_design = DesignDocument(
        version=2,
        title="Customer Portal Integration Design",
        description="Secure integration between customer portal and Salesforce CRM",
        architecture_overview="API-first architecture using MuleSoft as integration layer",
        components=[
            {"name": "API Gateway", "type": "security"},
            {"name": "Data Transformation Service", "type": "integration"},
            {"name": "Salesforce Connector", "type": "connector"},
        ],
        nfr_considerations={
            "performance": "Sub-500ms response time",
            "scalability": "Handle 10k requests/hour",
        },
        security_considerations={
            "authentication": "OAuth 2.0",
            "encryption": "TLS 1.3",
        },
        integration_points=[
            {"name": "Portal → API Gateway", "protocol": "HTTPS"},
            {"name": "API Gateway → Salesforce", "protocol": "HTTPS"},
        ],
        deployment_notes="Deploy to CloudHub 2.0 with auto-scaling enabled",
    )
    
    # Add reviewer feedback
    state.reviews = [
        ReviewFeedback(
            reviewer_role=AgentRole.REVIEWER_SECURITY,
            decision=ReviewDecision.REVISE,
            concerns=["Missing rate limiting", "Insufficient input validation"],
            suggestions=["Add API rate limiting", "Implement comprehensive input validation"],
            rationale="Security must be strengthened before deployment",
            severity="high",
        ),
        ReviewFeedback(
            reviewer_role=AgentRole.REVIEWER_NFR,
            decision=ReviewDecision.APPROVE,
            concerns=[],
            suggestions=["Consider caching for improved performance"],
            rationale="Architecture meets NFR requirements",
            severity="low",
        ),
    ]
    
    # Add debate outcome
    disagreement = Disagreement(
        disagreement_id="dis-001",
        agent_roles=[AgentRole.REVIEWER_NFR, AgentRole.REVIEWER_INTEGRATION],
        topic="Synchronous vs Asynchronous Processing",
        positions={
            AgentRole.REVIEWER_NFR.value: "Async for better scalability",
            AgentRole.REVIEWER_INTEGRATION.value: "Sync for simpler implementation",
        },
        severity="medium",
        category="performance_tradeoff",
    )
    
    state.debates = [
        DebateOutcome(
            debate_id="debate-001",
            disagreement=disagreement,
            debate_rounds=2,
            agent_positions_revised={
                AgentRole.REVIEWER_NFR.value: "Async with proper monitoring",
                AgentRole.REVIEWER_INTEGRATION.value: "Async agreed with fallback strategy",
            },
            consensus_reached=True,
            resolution_summary="Async processing selected for better scalability",
            confidence=0.85,
        )
    ]
    
    # Add consensus
    state.consensus_history = [
        ConsensusResult(
            round_id="round-1",
            agreed=True,
            confidence=0.85,
            summary="Strong consensus achieved across all reviewers",
            disagreements_resolved=["dis-001"],
            disagreements_unresolved=[],
            vote_breakdown={
                AgentRole.SOLUTION_ARCHITECT.value: "approve",
                AgentRole.REVIEWER_SECURITY.value: "approve",
                AgentRole.REVIEWER_NFR.value: "approve",
            },
            weights_applied={
                AgentRole.SOLUTION_ARCHITECT.value: 0.6,
                AgentRole.REVIEWER_SECURITY.value: 0.2,
                AgentRole.REVIEWER_NFR.value: 0.2,
            },
        )
    ]
    
    # Add final rationale
    state.final_architecture_rationale = "Architecture approved with security enhancements. Async processing pattern selected for optimal scalability."
    
    # Add FAQ entries
    state.faq_entries = [
        {"question": "Why OAuth 2.0?", "answer": "Industry standard, secure, widely supported"},
        {"question": "Why CloudHub 2.0?", "answer": "Auto-scaling, managed services, high availability"},
    ]
    
    return state


def test_build_architecture_summary(sample_workflow_state):
    """Test architecture summary generation."""
    summary = build_architecture_summary(sample_workflow_state)
    
    assert summary is not None
    assert len(summary.overview) > 0
    assert "Architecture approved" in summary.overview or "customer portal" in summary.overview.lower()
    assert len(summary.key_capabilities) > 0
    assert len(summary.non_functional_highlights) > 0
    
    # Check that capabilities include components
    capability_names = " ".join(summary.key_capabilities).lower()
    assert any(comp["name"].lower() in capability_names for comp in sample_workflow_state.current_design.components)


def test_build_decision_records(sample_workflow_state):
    """Test decision records generation."""
    decisions = build_decision_records(sample_workflow_state)
    
    assert decisions is not None
    assert len(decisions) >= 2  # At minimum should have some decisions
    
    # Check decision structure
    for decision in decisions:
        assert decision.id.startswith("ADR-")
        assert len(decision.title) > 0
        assert len(decision.context) > 0
        assert len(decision.decision) > 0
        assert len(decision.rationale) > 0
        assert len(decision.consequences) > 0
    
    # Check that debate topic appears in decisions
    decision_texts = " ".join([d.title + d.context for d in decisions])
    assert "Synchronous" in decision_texts or "Async" in decision_texts


def test_build_risks_and_mitigations(sample_workflow_state):
    """Test risk generation from reviewer concerns."""
    risks = build_risks_and_mitigations(sample_workflow_state)
    
    assert risks is not None
    assert len(risks) >= 2  # Should have at least a few risks
    
    # Check risk structure
    for risk in risks:
        assert risk.id.startswith("RISK-")
        assert len(risk.description) > 0
        assert risk.impact in ["low", "medium", "high", "critical"]
        assert risk.likelihood in ["low", "medium", "high"]
        assert len(risk.mitigation) > 0
    
    # Check that security concern appears as a risk
    risk_descriptions = " ".join([r.description.lower() for r in risks])
    assert "rate limiting" in risk_descriptions or "security" in risk_descriptions or "auth" in risk_descriptions


def test_build_faq_items(sample_workflow_state):
    """Test FAQ generation."""
    faqs = build_faq_items(sample_workflow_state)
    
    assert faqs is not None
    assert len(faqs) >= 2  # Should have several FAQs
    
    # Check FAQ structure
    for faq in faqs:
        assert len(faq.question) > 0
        assert len(faq.answer) > 0
        assert faq.source in ["adjudicator", "debate_outcome", "reviewer", "faq_agent", "platform_architect", "ops_reviewer"]
    
    # Check that existing FAQs are included
    faq_questions = " ".join([f.question for f in faqs])
    assert "OAuth" in faq_questions or "CloudHub" in faq_questions


def test_build_diagram_descriptors_demo_mode(sample_workflow_state):
    """Test diagram generation in demo mode."""
    diagrams = build_diagram_descriptors(
        state=sample_workflow_state,
        lucid_client=None,
        demo_mode=True,
    )
    
    assert diagrams is not None
    assert len(diagrams) >= 3  # Should have context, integration, deployment
    
    # Check diagram structure
    diagram_types = [d.diagram_type for d in diagrams]
    assert "context" in diagram_types
    assert "integration_flow" in diagram_types
    assert "deployment" in diagram_types
    
    # In demo mode, all diagrams should have Mermaid source
    for diagram in diagrams:
        assert diagram.title is not None
        assert diagram.description is not None
        assert diagram.mermaid_source is not None  # Should have Mermaid fallback
        assert "graph" in diagram.mermaid_source.lower() or "sequencediagram" in diagram.mermaid_source.lower()


def test_build_diagram_descriptors_with_lucid(sample_workflow_state):
    """Test diagram generation with Lucid client (mock)."""
    mock_lucid = Mock()
    mock_lucid.generate_architecture_diagrams = Mock(return_value={})
    
    diagrams = build_diagram_descriptors(
        state=sample_workflow_state,
        lucid_client=mock_lucid,
        demo_mode=False,
    )
    
    assert diagrams is not None
    assert len(diagrams) >= 3


def test_assemble_markdown_report():
    """Test markdown report assembly."""
    from app.graph.state_models import (
        ArchitectureSummary,
        DecisionRecord,
        RiskItem,
        FAQItem,
        DiagramDescriptor,
        DeliverablesBundle,
    )
    
    # Create a sample bundle
    bundle = DeliverablesBundle(
        session_id="test-123",
        architecture_summary=ArchitectureSummary(
            overview="Test architecture overview",
            key_capabilities=["API Gateway", "Data Transformation"],
            non_functional_highlights=["Scalability", "Security"],
        ),
        decisions=[
            DecisionRecord(
                id="ADR-001",
                title="API-First Design",
                context="Multiple integration points required",
                decision="Adopt API-first architecture",
                rationale="Enables loose coupling and reusability",
                consequences="All integrations go through API layer",
            )
        ],
        risks=[
            RiskItem(
                id="RISK-001",
                description="API downtime risk",
                impact="high",
                likelihood="medium",
                mitigation="Implement circuit breakers and fallbacks",
            )
        ],
        faqs=[
            FAQItem(
                question="Why API-first?",
                answer="Best practice for integration",
                source="architect",
            )
        ],
        diagrams=[
            DiagramDescriptor(
                diagram_type="context",
                title="System Context",
                description="High-level view",
                mermaid_source="graph TD\nA --> B",
            )
        ],
        generated_at=datetime.utcnow(),
    )
    
    markdown = assemble_markdown_report(bundle)
    
    assert markdown is not None
    assert len(markdown) > 0
    assert "# Architecture Deliverables" in markdown
    assert "## Architecture Summary" in markdown
    assert "## Key Design Decisions" in markdown
    assert "## Risks & Mitigations" in markdown
    assert "## FAQ" in markdown
    assert "## Architecture Diagrams" in markdown
    assert "ADR-001" in markdown
    assert "RISK-001" in markdown


def test_build_deliverables_bundle(sample_workflow_state):
    """Test complete deliverables bundle generation."""
    bundle = build_deliverables_bundle(
        state=sample_workflow_state,
        lucid_client=None,
        demo_mode=True,
    )
    
    assert bundle is not None
    assert bundle.session_id == "test-session-123"
    assert bundle.demo_mode is True
    assert bundle.workflow_version == "3.0-Phase3C"
    
    # Check all sections are populated
    assert bundle.architecture_summary is not None
    assert len(bundle.decisions) > 0
    assert len(bundle.risks) > 0
    assert len(bundle.faqs) > 0
    assert len(bundle.diagrams) > 0
    assert len(bundle.markdown_report) > 0
    
    # Check markdown report includes key content
    assert "Architecture Deliverables" in bundle.markdown_report
    assert bundle.session_id in bundle.markdown_report


def test_deliverables_with_minimal_state():
    """Test deliverables generation with minimal workflow state."""
    minimal_state = WorkflowState(
        session_id="minimal-123",
        user_request="Simple test request",
        status=WorkflowStatus.COMPLETED,
    )
    
    # Should still generate deliverables with fallback content
    bundle = build_deliverables_bundle(
        state=minimal_state,
        lucid_client=None,
        demo_mode=True,
    )
    
    assert bundle is not None
    assert len(bundle.decisions) >= 1  # Should have at least fallback decisions
    assert len(bundle.risks) >= 3  # Should have standard risks
    assert len(bundle.faqs) >= 2  # Should have fallback FAQs
    assert len(bundle.diagrams) >= 3  # Should have standard diagrams


def test_deliverables_markdown_download_format():
    """Test that markdown report is properly formatted for download."""
    state = WorkflowState(
        session_id="download-test",
        user_request="Test request",
        status=WorkflowStatus.COMPLETED,
    )
    
    bundle = build_deliverables_bundle(state, None, True)
    markdown = bundle.markdown_report
    
    # Check markdown has proper structure
    assert markdown.startswith("# ")
    assert "##" in markdown  # Has subheadings
    assert "|" in markdown  # Has tables (for risks)
    assert "```" in markdown  # Has code blocks (for diagrams)
    assert "\n" in markdown  # Has line breaks


def test_deliverables_idempotency(sample_workflow_state):
    """Test that generating deliverables multiple times produces consistent results."""
    bundle1 = build_deliverables_bundle(sample_workflow_state, None, True)
    bundle2 = build_deliverables_bundle(sample_workflow_state, None, True)
    
    # Should have same number of items (deterministic)
    assert len(bundle1.decisions) == len(bundle2.decisions)
    assert len(bundle1.risks) == len(bundle2.risks)
    assert len(bundle1.faqs) == len(bundle2.faqs)
    assert len(bundle1.diagrams) == len(bundle2.diagrams)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

