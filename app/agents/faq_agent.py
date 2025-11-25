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

    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute FAQ Agent logic.

        Args:
            input_data: Council discussion and decisions

        Returns:
            FAQ entries and decision rationale

        TODO: Implement full FAQ generation logic in Phase 2
        """
        try:
            logger.info("faq_agent_processing")

            # TODO: Phase 2 - Extract FAQ from discussion history
            # TODO: Phase 2 - Generate decision rationale
            # TODO: Phase 2 - Create knowledge base entries
            # TODO: Phase 2 - Integrate with NotebookLM for summaries

            prompt = f"""
From the following council discussion, extract:

Discussion: {input_data.request}

Context: {json.dumps(input_data.context, indent=2)}

Generate:
1. FAQ entries (questions and answers from the discussion)
2. Decision rationale (why certain architectural choices were made)
3. Key takeaways for stakeholders
4. Trade-offs and alternatives considered

Format as structured JSON with:
- faq_entries: list of {question, answer, category}
- decision_rationale: detailed explanation
- key_takeaways: list of important points
- trade_offs: list of {decision, alternatives, rationale}
"""

            response = self.generate_with_safety(
                user_prompt=prompt,
                json_mode=True,
            )

            logger.info("faq_agent_completed")

            return AgentOutput(
                content=response,
                metadata={"agent": "faq", "source": "council_discussion"},
                success=True
            )

        except Exception as e:
            logger.error("faq_agent_error", error=str(e))
            raise AgentExecutionException(
                f"FAQ Agent execution failed: {str(e)}",
                details={"agent": "faq"}
            )

