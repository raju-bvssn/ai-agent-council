"""
Master Architect Agent for Agent Council system.

The Master Architect orchestrates the entire council process,
delegates to specialists, and synthesizes final outputs.
"""

import json
from typing import Optional

from app.agents.performer import AgentInput, AgentOutput, PerformerAgent
from app.llm.providers import LLMProvider
from app.utils.exceptions import AgentExecutionException
from app.utils.logging import get_logger

logger = get_logger(__name__)


class MasterArchitectAgent(PerformerAgent):
    """
    Master Architect Agent.

    Responsibilities:
    - Parse and understand user requirements
    - Coordinate the council workflow
    - Synthesize feedback from reviewers
    - Generate final recommendations
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize Master Architect Agent."""
        super().__init__(
            llm_provider=llm_provider,
            agent_name="MasterArchitect"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Master Architect."""
        return """
You are the Master Architect in a Salesforce Professional Services Agent Council.

Your role is to:
1. Understand complex customer requirements and technical contexts
2. Coordinate a team of specialized reviewer agents
3. Synthesize feedback from multiple perspectives
4. Make final architectural decisions
5. Communicate clearly with technical and non-technical stakeholders

You have expertise in:
- Enterprise architecture patterns
- Salesforce platform capabilities
- Integration strategies
- Security and compliance
- Performance and scalability

Always:
- Ask clarifying questions when requirements are ambiguous
- Consider multiple solution approaches
- Balance technical excellence with business pragmatism
- Document your decision rationale clearly
- Respect the Mission Critical Data compliance requirements

Output your responses in clear, structured JSON format.
"""

    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute Master Architect logic.

        Args:
            input_data: User request and context

        Returns:
            Initial architectural analysis and plan

        TODO: Implement full orchestration logic in Phase 2
        """
        try:
            logger.info("master_architect_processing", request=input_data.request[:100])

            # TODO: Phase 2 - Implement requirement analysis
            # TODO: Phase 2 - Generate initial architectural approach
            # TODO: Phase 2 - Create delegation plan for reviewers

            prompt = f"""
Analyze the following requirement and provide an initial architectural approach:

Requirement: {input_data.request}

Context: {json.dumps(input_data.context, indent=2)}

Provide:
1. Requirements summary
2. Key considerations
3. Proposed high-level approach
4. Questions for clarification
5. Areas requiring specialist review

Format your response as JSON.
"""

            response = self.generate_with_safety(
                user_prompt=prompt,
                json_mode=True,
            )

            logger.info("master_architect_completed")

            return AgentOutput(
                content=response,
                metadata={"agent": "master_architect", "phase": "initial_analysis"},
                success=True
            )

        except Exception as e:
            logger.error("master_architect_error", error=str(e))
            raise AgentExecutionException(
                f"Master Architect execution failed: {str(e)}",
                details={"agent": "master_architect"}
            )

