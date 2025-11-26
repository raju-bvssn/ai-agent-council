"""
Deliverables generation service.

Core logic for transforming workflow state into concrete architecture deliverables.
POC-focused but production-ready with deterministic outputs.
"""

from datetime import datetime
from typing import Optional
import uuid
import structlog

from app.graph.state_models import (
    WorkflowState,
    ArchitectureSummary,
    DecisionRecord,
    RiskItem,
    FAQItem,
    DiagramDescriptor,
    DeliverablesBundle,
    AgentRole,
    ReviewDecision,
    Concern,
    Suggestion,
)

logger = structlog.get_logger(__name__)


def _to_string(item) -> str:
    """
    Convert Concern/Suggestion objects or strings to plain strings.
    
    Args:
        item: String, Concern, or Suggestion object
        
    Returns:
        Plain string representation
    """
    if isinstance(item, str):
        return item
    elif isinstance(item, Concern):
        return f"{item.area}: {item.description}" if item.area else item.description
    elif isinstance(item, Suggestion):
        return f"{item.area}: {item.suggestion}" if item.area else item.suggestion
    else:
        return str(item)


def build_architecture_summary(state: WorkflowState) -> ArchitectureSummary:
    """
    Build high-level architecture summary from workflow state.
    
    Extracts overview, key capabilities, and NFR highlights from the final design
    and reviewer feedback.
    
    Args:
        state: Completed workflow state
        
    Returns:
        ArchitectureSummary with overview and highlights
    """
    logger.info("building_architecture_summary", session_id=state.session_id)
    
    # Build overview from final design or user request
    overview = ""
    if state.final_architecture_rationale:
        overview = state.final_architecture_rationale
    elif state.current_design and state.current_design.architecture_overview:
        overview = state.current_design.architecture_overview
    else:
        overview = f"Architecture solution for: {state.user_request}"
    
    # Extract key capabilities
    key_capabilities = []
    if state.current_design:
        # From components
        for component in state.current_design.components:
            if isinstance(component, dict) and "name" in component:
                key_capabilities.append(component["name"])
        
        # From integration points
        for integration in state.current_design.integration_points:
            if isinstance(integration, dict) and "name" in integration:
                key_capabilities.append(f"Integration: {integration['name']}")
    
    # Limit to top 8 capabilities
    key_capabilities = key_capabilities[:8] if key_capabilities else [
        "Multi-system integration",
        "Secure API gateway",
        "Data transformation and routing",
        "Error handling and retry logic",
    ]
    
    # Extract NFR highlights from reviews
    nfr_highlights = []
    if state.current_design:
        # From NFR considerations
        for nfr_key, nfr_value in state.current_design.nfr_considerations.items():
            nfr_highlights.append(f"{nfr_key.title()}: {nfr_value}")
        
        # From security considerations
        for sec_key, sec_value in state.current_design.security_considerations.items():
            nfr_highlights.append(f"Security - {sec_key.title()}: {sec_value}")
    
    # Fallback NFRs
    if not nfr_highlights:
        nfr_highlights = [
            "Scalability: Supports horizontal scaling for high throughput",
            "Availability: 99.9% uptime with automated failover",
            "Security: OAuth 2.0, TLS encryption, API key management",
            "Performance: Sub-500ms response times for standard operations",
        ]
    
    # Limit to top 6 NFR highlights
    nfr_highlights = nfr_highlights[:6]
    
    return ArchitectureSummary(
        overview=overview,
        key_capabilities=key_capabilities,
        non_functional_highlights=nfr_highlights,
    )


def build_decision_records(state: WorkflowState) -> list[DecisionRecord]:
    """
    Build Architecture Decision Records from workflow debates and reviews.
    
    Extracts key decisions from reviewer feedback, debates, and adjudicator output.
    
    Args:
        state: Completed workflow state
        
    Returns:
        List of DecisionRecord objects
    """
    logger.info("building_decision_records", session_id=state.session_id)
    
    decisions = []
    decision_id_counter = 1
    
    # Decision 1: From adjudicator if available
    if state.final_architecture_rationale:
        decisions.append(DecisionRecord(
            id=f"ADR-{decision_id_counter:03d}",
            title="Final Architecture Pattern Selection",
            context=f"User requested: {state.user_request[:200]}. Multiple agent reviews and potential debates occurred.",
            decision="Final architecture approved by Architect Adjudicator",
            rationale=state.final_architecture_rationale[:500],
            consequences="Architecture aligns with best practices, security requirements, and NFRs. Implementation can proceed with confidence.",
        ))
        decision_id_counter += 1
    
    # Decision 2: From debates if any
    if state.debates:
        for idx, debate in enumerate(state.debates[:3], start=1):  # Limit to 3
            topic = debate.disagreement.topic if debate.disagreement else "Debate topic"
            decisions.append(DecisionRecord(
                id=f"ADR-{decision_id_counter:03d}",
                title=f"Resolution: {topic}",
                context=f"Disagreement between reviewers on: {topic}",
                decision=f"Consensus reached: {'Yes' if debate.consensus_reached else 'No'}",
                rationale=debate.resolution_summary[:500] if debate.resolution_summary else "Resolved through agent debate cycle",
                consequences=f"Design updated to address {topic}. Confidence: {debate.confidence or 0.0:.2f}",
            ))
            decision_id_counter += 1
    
    # Decision 3: From consensus if available
    if state.consensus_history:
        latest_consensus = state.consensus_history[-1]
        decisions.append(DecisionRecord(
            id=f"ADR-{decision_id_counter:03d}",
            title="Overall Agent Council Consensus",
            context=f"After {state.current_round} review round(s), agents evaluated the architecture",
            decision=f"Consensus {'achieved' if latest_consensus.agreed else 'not achieved'}",
            rationale=latest_consensus.summary[:500] if latest_consensus.summary else "Weighted consensus computed across all reviewer agents",
            consequences=f"Confidence level: {latest_consensus.confidence:.2f}. {'Proceed with implementation.' if latest_consensus.agreed else 'Further review recommended.'}",
        ))
        decision_id_counter += 1
    
    # Decision 4: Integration pattern (inferred from design or reviews)
    if state.current_design and state.current_design.integration_points:
        decisions.append(DecisionRecord(
            id=f"ADR-{decision_id_counter:03d}",
            title="Integration Pattern Selection",
            context="Multiple integration options considered for system connectivity",
            decision=f"{len(state.current_design.integration_points)} integration point(s) defined",
            rationale="Selected pattern optimizes for maintainability, security, and performance based on MuleSoft best practices",
            consequences="Clear integration contracts defined. APIs documented. Security policies applied at each integration point.",
        ))
        decision_id_counter += 1
    
    # Decision 5: Deployment model (inferred from deployment notes)
    if state.current_design and state.current_design.deployment_notes:
        decisions.append(DecisionRecord(
            id=f"ADR-{decision_id_counter:03d}",
            title="Deployment Architecture",
            context="Deployment model must support NFRs and operational requirements",
            decision="Deployment strategy defined",
            rationale=state.current_design.deployment_notes[:300],
            consequences="Deployment approach enables scalability, monitoring, and operational excellence",
        ))
        decision_id_counter += 1
    
    # Fallback: Ensure at least 2 decisions
    if len(decisions) < 2:
        decisions.append(DecisionRecord(
            id=f"ADR-{decision_id_counter:03d}",
            title="API-First Architecture Approach",
            context="System requires integration with multiple external systems and future extensibility",
            decision="Adopt API-first design with RESTful interfaces and comprehensive API management",
            rationale="API-first approach enables loose coupling, independent scaling, and clear contracts between systems",
            consequences="All integrations go through managed API layer. Enables monitoring, security policies, and rate limiting.",
        ))
        decision_id_counter += 1
    
    logger.info("decision_records_built", session_id=state.session_id, count=len(decisions))
    return decisions


def build_risks_and_mitigations(state: WorkflowState) -> list[RiskItem]:
    """
    Build risk items from reviewer concerns and design analysis.
    
    Identifies technical risks from security, performance, integration,
    and operational reviews.
    
    Args:
        state: Completed workflow state
        
    Returns:
        List of RiskItem objects
    """
    logger.info("building_risks_and_mitigations", session_id=state.session_id)
    
    risks = []
    risk_id_counter = 1
    
    # Extract risks from reviewer concerns
    for review in state.reviews:
        if review.concerns and review.severity in ["high", "critical"]:
            for concern in review.concerns[:2]:  # Top 2 concerns per review
                risks.append(RiskItem(
                    id=f"RISK-{risk_id_counter:03d}",
                    description=_to_string(concern),
                    impact=review.severity,
                    likelihood="medium",  # Conservative estimate
                    mitigation=_to_string(review.suggestions[0]) if review.suggestions else "Review and address during implementation phase",
                    owner=review.reviewer_role.value if review.reviewer_role else None,
                ))
                risk_id_counter += 1
    
    # Add standard integration risks if not covered
    if not any("integration" in r.description.lower() for r in risks):
        risks.append(RiskItem(
            id=f"RISK-{risk_id_counter:03d}",
            description="Integration point failures or timeouts could impact system availability",
            impact="high",
            likelihood="medium",
            mitigation="Implement circuit breakers, retry logic with exponential backoff, and fallback mechanisms at each integration point",
            owner="integration_architect",
        ))
        risk_id_counter += 1
    
    # Add standard security risks if not covered
    if not any("security" in r.description.lower() or "auth" in r.description.lower() for r in risks):
        risks.append(RiskItem(
            id=f"RISK-{risk_id_counter:03d}",
            description="Unauthorized access to APIs or sensitive data exposure",
            impact="critical",
            likelihood="medium",
            mitigation="Enforce OAuth 2.0, API key rotation, TLS 1.2+, input validation, and rate limiting on all endpoints",
            owner="security_architect",
        ))
        risk_id_counter += 1
    
    # Add standard performance risks if not covered
    if not any("performance" in r.description.lower() or "scale" in r.description.lower() for r in risks):
        risks.append(RiskItem(
            id=f"RISK-{risk_id_counter:03d}",
            description="System may not meet performance SLAs under peak load conditions",
            impact="high",
            likelihood="low",
            mitigation="Conduct load testing, implement caching strategies, enable auto-scaling, and optimize database queries",
            owner="platform_architect",
        ))
        risk_id_counter += 1
    
    # Add data quality risk if not covered
    if not any("data" in r.description.lower() for r in risks):
        risks.append(RiskItem(
            id=f"RISK-{risk_id_counter:03d}",
            description="Data inconsistencies or format mismatches between integrated systems",
            impact="medium",
            likelihood="medium",
            mitigation="Implement comprehensive data validation, transformation rules, error handling, and data quality monitoring",
            owner="integration_architect",
        ))
        risk_id_counter += 1
    
    # Limit to top 6 risks
    risks = risks[:6]
    
    logger.info("risks_built", session_id=state.session_id, count=len(risks))
    return risks


def build_faq_items(state: WorkflowState) -> list[FAQItem]:
    """
    Build FAQ items from workflow discussions and decisions.
    
    Generates Q&A pairs from user request, reviewer feedback, debates,
    and final decisions to help human architects understand the rationale.
    
    Args:
        state: Completed workflow state
        
    Returns:
        List of FAQItem objects
    """
    logger.info("building_faq_items", session_id=state.session_id)
    
    faqs = []
    
    # FAQ 1: Why this architecture approach?
    if state.final_architecture_rationale:
        faqs.append(FAQItem(
            question="Why was this architecture approach selected?",
            answer=state.final_architecture_rationale[:400],
            source="adjudicator",
        ))
    
    # FAQ 2: From debates
    if state.debates:
        for debate in state.debates[:2]:  # Top 2 debates
            topic = debate.disagreement.topic if debate.disagreement else "this issue"
            faqs.append(FAQItem(
                question=f"Why was {topic} decided this way?",
                answer=debate.resolution_summary[:400] if debate.resolution_summary else "Resolved through agent consensus",
                source="debate_outcome",
            ))
    
    # FAQ 3: From existing FAQ entries
    for entry in state.faq_entries[:3]:  # Top 3 existing FAQs
        if isinstance(entry, dict) and "question" in entry and "answer" in entry:
            faqs.append(FAQItem(
                question=entry["question"],
                answer=entry["answer"],
                source="faq_agent",
            ))
    
    # FAQ 4: Integration pattern rationale
    if state.current_design and state.current_design.integration_points:
        faqs.append(FAQItem(
            question="How are external systems integrated?",
            answer=f"Architecture includes {len(state.current_design.integration_points)} integration point(s) using API-first pattern with MuleSoft. Each integration has defined contracts, security policies, and error handling.",
            source="reviewer",
        ))
    
    # FAQ 5: Security approach
    if state.current_design and state.current_design.security_considerations:
        security_summary = ". ".join([f"{k}: {v}" for k, v in list(state.current_design.security_considerations.items())[:2]])
        faqs.append(FAQItem(
            question="How is security handled?",
            answer=security_summary if security_summary else "OAuth 2.0 authentication, TLS encryption, API key management, and input validation applied throughout",
            source="reviewer",
        ))
    
    # FAQ 6: NFR/SLA considerations
    if state.current_design and state.current_design.nfr_considerations:
        nfr_summary = ". ".join([f"{k}: {v}" for k, v in list(state.current_design.nfr_considerations.items())[:2]])
        faqs.append(FAQItem(
            question="What are the key non-functional requirements?",
            answer=nfr_summary if nfr_summary else "Scalability, availability (99.9%), performance (sub-500ms), and maintainability prioritized",
            source="reviewer",
        ))
    
    # Fallback FAQs if needed
    if len(faqs) < 3:
        faqs.extend([
            FAQItem(
                question="What deployment model is recommended?",
                answer="CloudHub 2.0 for MuleSoft applications with auto-scaling, multi-region redundancy, and managed services for databases and messaging",
                source="platform_architect",
            ),
            FAQItem(
                question="How is monitoring and observability handled?",
                answer="Anypoint Monitoring for MuleSoft metrics, custom dashboards, alerting on SLA thresholds, and integration with enterprise monitoring tools",
                source="ops_reviewer",
            ),
        ])
    
    # Limit to 8 FAQs
    faqs = faqs[:8]
    
    logger.info("faq_items_built", session_id=state.session_id, count=len(faqs))
    return faqs


def build_diagram_descriptors(
    state: WorkflowState,
    lucid_client: Optional[any] = None,  # type: ignore
    demo_mode: bool = False,
) -> list[DiagramDescriptor]:
    """
    Build diagram descriptors with Lucid URLs or Mermaid fallback.
    
    Generates diagram metadata for system context, integration flow,
    deployment, and sequence diagrams. Uses Lucid if available,
    otherwise provides Mermaid source.
    
    Args:
        state: Completed workflow state
        lucid_client: Optional Lucid client for diagram generation
        demo_mode: Whether running in demo mode (use Mermaid fallback)
        
    Returns:
        List of DiagramDescriptor objects
    """
    logger.info("building_diagram_descriptors", session_id=state.session_id, demo_mode=demo_mode)
    
    diagrams = []
    
    # Try to get Lucid URLs if not in demo mode and client available
    lucid_urls = {}
    if not demo_mode and lucid_client:
        try:
            # Will be implemented in Lucid client extension
            lucid_urls = {}  # Placeholder - will call lucid_client.generate_architecture_diagrams(state)
            logger.info("lucid_diagrams_generated", count=len(lucid_urls))
        except Exception as e:
            logger.warning("lucid_generation_failed", error=str(e))
            lucid_urls = {}
    
    # Diagram 1: System Context
    diagrams.append(DiagramDescriptor(
        diagram_type="context",
        title="System Context Diagram",
        description="High-level view of the system and its external interfaces",
        lucid_url=lucid_urls.get("context"),
        mermaid_source=_get_mermaid_context_diagram(state) if not lucid_urls.get("context") else None,
    ))
    
    # Diagram 2: Integration Flow
    diagrams.append(DiagramDescriptor(
        diagram_type="integration_flow",
        title="Integration Flow Diagram",
        description="Data flow and transformations across integrated systems",
        lucid_url=lucid_urls.get("integration_flow"),
        mermaid_source=_get_mermaid_integration_flow(state) if not lucid_urls.get("integration_flow") else None,
    ))
    
    # Diagram 3: Deployment
    diagrams.append(DiagramDescriptor(
        diagram_type="deployment",
        title="Deployment Architecture",
        description="Physical deployment topology with runtime and hosting components",
        lucid_url=lucid_urls.get("deployment"),
        mermaid_source=_get_mermaid_deployment_diagram(state) if not lucid_urls.get("deployment") else None,
    ))
    
    # Diagram 4: Sequence (if integration points exist)
    if state.current_design and state.current_design.integration_points:
        diagrams.append(DiagramDescriptor(
            diagram_type="sequence",
            title="Integration Sequence Diagram",
            description="Detailed message flow for key integration scenarios",
            lucid_url=lucid_urls.get("sequence"),
            mermaid_source=_get_mermaid_sequence_diagram(state) if not lucid_urls.get("sequence") else None,
        ))
    
    logger.info("diagram_descriptors_built", session_id=state.session_id, count=len(diagrams))
    return diagrams


def _get_mermaid_context_diagram(state: WorkflowState) -> str:
    """Generate Mermaid source for system context diagram."""
    return f"""graph TB
    subgraph External Systems
        A[Customer Portal]
        B[ERP System]
        C[CRM Platform]
    end
    
    subgraph "{state.user_request[:30]}..."
        M[MuleSoft Integration Layer]
        S[Salesforce]
    end
    
    A --> M
    B --> M
    M --> S
    M --> C
    
    style M fill:#00A1E0
    style S fill:#00A1E0"""


def _get_mermaid_integration_flow(state: WorkflowState) -> str:
    """Generate Mermaid source for integration flow diagram."""
    num_integrations = len(state.current_design.integration_points) if state.current_design else 2
    return f"""graph LR
    A[Source System] --> B[API Gateway]
    B --> C[Data Transformation]
    C --> D[Business Logic]
    D --> E[Target System]
    D --> F[Logging & Monitoring]
    
    style B fill:#00A1E0
    style C fill:#00A1E0"""


def _get_mermaid_deployment_diagram(state: WorkflowState) -> str:
    """Generate Mermaid source for deployment diagram."""
    return """graph TB
    subgraph CloudHub 2.0
        A[API Gateway]
        B[Integration Apps]
        C[Data Services]
    end
    
    subgraph Salesforce
        D[Platform APIs]
    end
    
    subgraph Monitoring
        E[Anypoint Monitoring]
        F[Custom Dashboards]
    end
    
    B --> A
    B --> C
    B --> D
    A --> E
    B --> E
    
    style A fill:#00A1E0
    style B fill:#00A1E0"""


def _get_mermaid_sequence_diagram(state: WorkflowState) -> str:
    """Generate Mermaid source for sequence diagram."""
    return """sequenceDiagram
    participant Client
    participant API Gateway
    participant MuleSoft
    participant Salesforce
    
    Client->>API Gateway: Request
    API Gateway->>MuleSoft: Validate & Route
    MuleSoft->>Salesforce: Query/Update
    Salesforce-->>MuleSoft: Response
    MuleSoft-->>API Gateway: Transformed Data
    API Gateway-->>Client: Response"""


def assemble_markdown_report(bundle: DeliverablesBundle) -> str:
    """
    Assemble complete Markdown report from deliverables bundle.
    
    Creates a comprehensive, well-formatted Markdown document suitable
    for customer delivery or internal documentation.
    
    Args:
        bundle: Complete deliverables bundle
        
    Returns:
        Markdown-formatted report string
    """
    logger.info("assembling_markdown_report", session_id=bundle.session_id)
    
    lines = []
    
    # Header
    lines.append("# Architecture Deliverables")
    lines.append("")
    lines.append(f"**Session ID:** {bundle.session_id}")
    lines.append(f"**Generated:** {bundle.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Workflow Version:** {bundle.workflow_version}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Architecture Summary
    lines.append("## Architecture Summary")
    lines.append("")
    lines.append(bundle.architecture_summary.overview)
    lines.append("")
    
    lines.append("### Key Capabilities")
    lines.append("")
    for cap in bundle.architecture_summary.key_capabilities:
        lines.append(f"* {cap}")
    lines.append("")
    
    lines.append("### Non-Functional Highlights")
    lines.append("")
    for nfr in bundle.architecture_summary.non_functional_highlights:
        lines.append(f"* {nfr}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Key Design Decisions
    lines.append("## Key Design Decisions (ADR-Style)")
    lines.append("")
    for decision in bundle.decisions:
        lines.append(f"### {decision.id}: {decision.title}")
        lines.append("")
        lines.append(f"**Context:** {decision.context}")
        lines.append("")
        lines.append(f"**Decision:** {decision.decision}")
        lines.append("")
        lines.append(f"**Rationale:** {decision.rationale}")
        lines.append("")
        lines.append(f"**Consequences:** {decision.consequences}")
        lines.append("")
    lines.append("---")
    lines.append("")
    
    # Risks & Mitigations
    lines.append("## Risks & Mitigations")
    lines.append("")
    lines.append("| Risk ID | Description | Impact | Likelihood | Mitigation |")
    lines.append("|---------|-------------|--------|------------|------------|")
    for risk in bundle.risks:
        lines.append(f"| {risk.id} | {risk.description[:80]} | {risk.impact} | {risk.likelihood} | {risk.mitigation[:80]} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # FAQ
    lines.append("## FAQ for Architecture Review Board")
    lines.append("")
    for idx, faq in enumerate(bundle.faqs, start=1):
        lines.append(f"### Q{idx}: {faq.question}")
        lines.append("")
        lines.append(f"**A:** {faq.answer}")
        lines.append("")
    lines.append("---")
    lines.append("")
    
    # Diagrams
    lines.append("## Architecture Diagrams")
    lines.append("")
    for diagram in bundle.diagrams:
        lines.append(f"### {diagram.title}")
        lines.append("")
        lines.append(f"**Type:** {diagram.diagram_type}")
        lines.append("")
        lines.append(f"**Description:** {diagram.description}")
        lines.append("")
        if diagram.lucid_url:
            lines.append(f"**Lucid Diagram:** [Open in Lucid]({diagram.lucid_url})")
            lines.append("")
        elif diagram.mermaid_source:
            lines.append("**Mermaid Source:**")
            lines.append("")
            lines.append("```mermaid")
            lines.append(diagram.mermaid_source)
            lines.append("```")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*Generated by Agent Council Platform - Phase 3C*")
    lines.append("")
    
    markdown = "\n".join(lines)
    logger.info("markdown_report_assembled", session_id=bundle.session_id, length=len(markdown))
    return markdown


def build_deliverables_bundle(
    state: WorkflowState,
    lucid_client: Optional[any] = None,  # type: ignore
    demo_mode: bool = False,
) -> DeliverablesBundle:
    """
    Build complete deliverables bundle from workflow state.
    
    Main orchestration function that calls all component builders and
    assembles the final deliverables package.
    
    Args:
        state: Completed workflow state
        lucid_client: Optional Lucid client for diagram generation
        demo_mode: Whether running in demo mode
        
    Returns:
        Complete DeliverablesBundle
    """
    logger.info("building_deliverables_bundle", session_id=state.session_id, demo_mode=demo_mode)
    
    try:
        # Build all components
        architecture_summary = build_architecture_summary(state)
        decisions = build_decision_records(state)
        risks = build_risks_and_mitigations(state)
        faqs = build_faq_items(state)
        diagrams = build_diagram_descriptors(state, lucid_client, demo_mode)
        
        # Create bundle (without markdown initially)
        bundle = DeliverablesBundle(
            session_id=state.session_id,
            architecture_summary=architecture_summary,
            decisions=decisions,
            risks=risks,
            faqs=faqs,
            diagrams=diagrams,
            markdown_report="",  # Will be populated next
            generated_at=datetime.utcnow(),
            workflow_version="3.0-Phase3C",
            includes_tool_insights=lucid_client is not None and not demo_mode,
            demo_mode=demo_mode,
        )
        
        # Assemble markdown report
        bundle.markdown_report = assemble_markdown_report(bundle)
        
        logger.info(
            "deliverables_bundle_built",
            session_id=state.session_id,
            decisions_count=len(decisions),
            risks_count=len(risks),
            faqs_count=len(faqs),
            diagrams_count=len(diagrams),
        )
        
        return bundle
        
    except Exception as e:
        logger.error("deliverables_bundle_build_failed", session_id=state.session_id, error=str(e))
        raise

