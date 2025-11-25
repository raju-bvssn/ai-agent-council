"""
Reviewer Agent implementations for Agent Council system.

Specialized reviewer agents for different aspects:
- NFR/Performance Reviewer
- Security Reviewer
- Integration Reviewer
- Domain Expert Reviewer
- Operations Reviewer
"""

import json
from typing import Optional

from app.agents.critic import CriticAgent, CriticInput, CriticOutput
from app.graph.state_models import ReviewDecision
from app.llm.providers import LLMProvider
from app.utils.exceptions import AgentExecutionException
from app.utils.logging import get_logger

logger = get_logger(__name__)


class NFRPerformanceReviewer(CriticAgent):
    """Reviewer focused on Non-Functional Requirements and Performance."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize NFR/Performance Reviewer."""
        super().__init__(
            llm_provider=llm_provider,
            agent_name="NFRPerformanceReviewer"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for NFR/Performance Reviewer."""
        return """
You are an NFR and Performance Specialist in a Salesforce PS Agent Council.

Focus areas:
- Performance and scalability requirements
- Response time and throughput expectations
- Resource utilization and optimization
- Caching strategies
- Governor limits in Salesforce
- Load handling and stress scenarios

Review designs for performance bottlenecks and scalability concerns.
"""

    def run(self, input_data: CriticInput) -> CriticOutput:
        """Execute NFR/Performance review."""
        try:
            logger.info("nfr_performance_review_started")

            review_criteria = """
**Performance & NFR Review Criteria:**

Analyze the design and provide structured feedback on:

1. **Performance Bottlenecks:**
   - Identify potential performance issues
   - Database query optimization
   - API call efficiency
   - Rendering and UI performance

2. **Scalability:**
   - Can this handle 10x current load?
   - Horizontal and vertical scaling considerations
   - Resource utilization patterns

3. **Salesforce Governor Limits:**
   - SOQL query limits (100 sync, 200 async)
   - DML statements (150 per transaction)
   - Heap size limits (6MB sync, 12MB async)
   - CPU time (10s sync, 60s async)
   - API call limits

4. **Caching & Optimization:**
   - Platform cache usage
   - Query optimization opportunities
   - Bulk processing patterns
   - Async processing where applicable

5. **Load Handling:**
   - Batch processing strategies
   - Rate limiting approaches
   - Queue management

**Decision Options:** "approve", "revise", "reject", "escalate"
**Severity Levels:** "low", "medium", "high", "critical"

Provide specific, actionable feedback.
"""

            response_text = self.generate_review(
                content=input_data.content_to_review,
                review_criteria=review_criteria
            )

            response = json.loads(response_text)

            logger.info("nfr_performance_review_completed", decision=response.get("decision"))

            return CriticOutput(
                decision=ReviewDecision(response.get("decision", "approve")),
                concerns=response.get("concerns", []),
                suggestions=response.get("suggestions", []),
                rationale=response.get("rationale", "No issues found"),
                severity=response.get("severity", "medium"),
                success=True
            )

        except Exception as e:
            logger.error("nfr_performance_review_error", error=str(e))
            raise AgentExecutionException(
                f"NFR review failed: {str(e)}",
                details={"reviewer": "nfr", "error_type": type(e).__name__}
            )


class SecurityReviewer(CriticAgent):
    """Reviewer focused on Security considerations."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize Security Reviewer."""
        super().__init__(
            llm_provider=llm_provider,
            agent_name="SecurityReviewer"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Security Reviewer."""
        return """
You are a Security Specialist in a Salesforce PS Agent Council.

Focus areas:
- Authentication and authorization
- Data encryption (at rest and in transit)
- Salesforce sharing and security model
- API security
- PII and sensitive data handling
- Compliance requirements (GDPR, HIPAA, etc.)
- Security best practices

Review designs for security vulnerabilities and compliance gaps.
"""

    def run(self, input_data: CriticInput) -> CriticOutput:
        """Execute Security review."""
        try:
            logger.info("security_review_started")

            review_criteria = """
**Security Review Criteria:**

Comprehensively analyze the design for security concerns:

1. **Authentication & Authorization:**
   - SSO and identity provider integration
   - OAuth 2.0 flows if applicable
   - Session management
   - Multi-factor authentication

2. **Salesforce Security Model:**
   - Profiles and permission sets
   - Object-level security (OLS)
   - Field-level security (FLS)
   - Sharing rules and role hierarchy
   - Record-level security

3. **Data Protection:**
   - Encryption at rest (Platform Encryption, Shield)
   - Encryption in transit (TLS/SSL)
   - PII and sensitive data handling
   - Data masking and anonymization
   - Backup and recovery security

4. **API Security:**
   - API authentication methods
   - Rate limiting and throttling
   - Input validation and sanitization
   - SQL injection prevention
   - Cross-site scripting (XSS) protection

5. **Compliance:**
   - GDPR compliance if applicable
   - HIPAA considerations for healthcare
   - SOC 2, ISO 27001 requirements
   - Data residency requirements
   - Audit trail and logging

6. **External Integrations:**
   - Named credentials and secure credential storage
   - Certificate management
   - IP whitelisting
   - VPN or private connectivity

**Decision Options:** "approve", "revise", "reject", "escalate"
**Severity for Security:** Prefer "high" or "critical" for security issues

Be thorough - security is mission-critical.
"""

            response_text = self.generate_review(
                content=input_data.content_to_review,
                review_criteria=review_criteria
            )

            response = json.loads(response_text)

            logger.info("security_review_completed", decision=response.get("decision"))

            return CriticOutput(
                decision=ReviewDecision(response.get("decision", "approve")),
                concerns=response.get("concerns", []),
                suggestions=response.get("suggestions", []),
                rationale=response.get("rationale", "Security posture acceptable"),
                severity=response.get("severity", "medium"),
                success=True
            )

        except Exception as e:
            logger.error("security_review_error", error=str(e))
            raise AgentExecutionException(
                f"Security review failed: {str(e)}",
                details={"reviewer": "security", "error_type": type(e).__name__}
            )


class IntegrationReviewer(CriticAgent):
    """Reviewer focused on Integration architecture."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize Integration Reviewer."""
        super().__init__(
            llm_provider=llm_provider,
            agent_name="IntegrationReviewer"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Integration Reviewer."""
        return """
You are an Integration Specialist in a Salesforce PS Agent Council.

Focus areas:
- API design and patterns
- MuleSoft and middleware integration
- Real-time vs batch integration
- Error handling and retry logic
- Data transformation and mapping
- Integration security
- Monitoring and observability

Review designs for integration complexity and reliability.
"""

    def run(self, input_data: CriticInput) -> CriticOutput:
        """Execute Integration review."""
        try:
            logger.info("integration_review_started")

            review_criteria = """
**Integration Architecture Review Criteria:**

Evaluate all integration aspects comprehensively:

1. **Integration Patterns:**
   - RESTful API design (Richardson Maturity Model)
   - SOAP web services if applicable
   - Event-driven architecture (Platform Events, Change Data Capture)
   - Batch/bulk data integration
   - Real-time vs asynchronous patterns
   - Request-reply vs fire-and-forget

2. **API Design:**
   - Endpoint design and versioning
   - Payload structure (JSON/XML)
   - HTTP methods and status codes
   - Pagination for large datasets
   - Idempotency for critical operations
   - API gateway usage

3. **Error Handling & Resilience:**
   - Retry logic with exponential backoff
   - Circuit breaker patterns
   - Dead letter queues
   - Transaction rollback strategies
   - Timeout configurations
   - Graceful degradation

4. **Data Transformation:**
   - Mapping complexity
   - Data validation rules
   - Format conversions (JSON, XML, CSV)
   - Field-level transformations
   - Lookup and enrichment logic

5. **Reliability & Performance:**
   - Connection pooling
   - Rate limiting and throttling
   - Bulk API usage where appropriate
   - Async processing for long-running operations
   - Queue management (Queueable, Batch)

6. **Monitoring & Observability:**
   - Integration logs and alerts
   - Success/failure metrics
   - Performance monitoring
   - End-to-end tracing
   - SLA tracking

7. **External System Considerations:**
   - System availability and SLAs
   - Authentication (OAuth, API keys, certificates)
   - Network connectivity (VPN, private link)
   - Firewall and IP whitelisting

**Decision Options:** "approve", "revise", "reject", "escalate"
**Severity Levels:** "low", "medium", "high", "critical"

Focus on integration reliability and maintainability.
"""

            response_text = self.generate_review(
                content=input_data.content_to_review,
                review_criteria=review_criteria
            )

            response = json.loads(response_text)

            logger.info("integration_review_completed", decision=response.get("decision"))

            return CriticOutput(
                decision=ReviewDecision(response.get("decision", "approve")),
                concerns=response.get("concerns", []),
                suggestions=response.get("suggestions", []),
                rationale=response.get("rationale", "Integration design acceptable"),
                severity=response.get("severity", "medium"),
                success=True
            )

        except Exception as e:
            logger.error("integration_review_error", error=str(e))
            raise AgentExecutionException(
                f"Integration review failed: {str(e)}",
                details={"reviewer": "integration", "error_type": type(e).__name__}
            )


# TODO: Phase 2 - Implement DomainExpertReviewer
# TODO: Phase 2 - Implement OperationsReviewer

