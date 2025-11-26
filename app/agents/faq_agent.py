"""
FAQ Agent for Agent Council system.

Generates FAQ entries and decision rationale documentation
from the council's discussions and decisions.
"""

import json
from typing import Optional

from app.agents.performer import AgentInput, AgentOutput, PerformerAgent
from app.llm.providers import LLMProvider
from app.utils.exceptions import AgentExecutionException
from app.utils.logging import get_logger

# LangSmith tracing (optional)
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

logger = get_logger(__name__)


class FAQAgent(PerformerAgent):
    """
    FAQ and Decision Rationale Agent.

    Responsibilities:
    - Extract key questions and answers from council discussions
    - Document decision rationale
    - Create knowledge base entries
    - Summarize review feedback
    - Generate stakeholder communications
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize FAQ Agent."""
        super().__init__(
            llm_provider=llm_provider,
            agent_name="FAQAgent"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for FAQ Agent."""
        return """
You are a Knowledge Management Specialist in a Salesforce PS Agent Council.

Your role is to:
1. Extract FAQs from technical discussions
2. Document architectural decisions and their rationale
3. Create clear, accessible knowledge base entries
4. Summarize complex technical concepts for different audiences
5. Generate stakeholder communications

Your outputs should be:
- Clear and concise
- Accessible to both technical and business audiences
- Well-structured and organized
- Focused on "why" decisions were made
- Traceable to source discussions

Always output in structured JSON format.
"""

    @traceable(name="faq_agent_run")
    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute FAQ Agent logic.

        Args:
            input_data: Council discussion and decisions

        Returns:
            FAQ entries and decision rationale

        """
        try:
            logger.info("faq_agent_processing")

            # Extract discussion context
            messages = input_data.context.get("messages", []) if input_data.context else []
            reviews = input_data.context.get("reviews", []) if input_data.context else []

            # Build comprehensive discussion summary
            discussion_summary = "**Agent Council Discussion Summary:**\n\n"
            
            for msg in messages:
                agent = msg.get("agent", "Unknown")
                content = msg.get("content", "")[:500]  # Truncate for context
                discussion_summary += f"- **{agent}:** {content}...\n\n"

            review_summary = "\n**Review Feedback:**\n\n"
            for review in reviews:
                reviewer = review.get("reviewer", "Unknown")
                decision = review.get("decision", "unknown")
                concerns = review.get("concerns", [])
                suggestions = review.get("suggestions", [])
                review_summary += f"- **{reviewer}** decided: {decision}\n"
                if concerns:
                    # Convert Concern objects to strings
                    concern_strs = [str(c) if not isinstance(c, str) else c for c in concerns]
                    review_summary += f"  Concerns: {', '.join(concern_strs)}\n"
                if suggestions:
                    # Convert Suggestion objects to strings
                    suggestion_strs = [str(s) if not isinstance(s, str) else s for s in suggestions]
                    review_summary += f"  Suggestions: {', '.join(suggestion_strs)}\n"

            prompt = f"""
As a Knowledge Management Specialist, analyze this Salesforce Agent Council discussion and create comprehensive documentation.

**Original Requirement:**
{input_data.request}

{discussion_summary}

{review_summary}

**Your Task:**
Generate documentation in JSON with faq_entries, decision_rationale, key_takeaways, trade_offs, risks_acknowledged, and next_steps.
Make FAQ entries practical. Explain the "why" behind architectural choices clearly.
"""

            response = self.generate_with_safety(
                user_prompt=prompt,
                json_mode=True,
                temperature=0.7
            )

            # Validate JSON
            try:
                json.loads(response)
            except json.JSONDecodeError as e:
                logger.warning("faq_agent_invalid_json", error=str(e))
                response = json.dumps({"documentation": response})

            logger.info("faq_agent_completed", message_count=len(messages), review_count=len(reviews))

            return AgentOutput(
                content=response,
                metadata={
                    "agent": "faq",
                    "source": "council_discussion",
                    "messages_processed": len(messages),
                    "reviews_processed": len(reviews),
                    "model": self.llm_provider.get_model_name()
                },
                success=True
            )

        except Exception as e:
            logger.error("faq_agent_error", error=str(e))
            raise AgentExecutionException(
                f"FAQ Agent execution failed: {str(e)}",
                details={"agent": "faq", "error_type": type(e).__name__}
            )

