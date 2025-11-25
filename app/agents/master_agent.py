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
        """
        try:
            logger.info("master_architect_processing", request=input_data.request[:100])

            # Build context string
            context_str = json.dumps(input_data.context, indent=2) if input_data.context else "No additional context provided"

            prompt = f"""
Analyze the following Salesforce solution requirement and provide an initial architectural approach:

**Customer Requirement:**
{input_data.request}

**Context:**
{context_str}

**Your Task:**
Provide a comprehensive initial analysis in the following JSON structure:
{{
  "requirements_summary": "Clear summary of what the customer needs",
  "key_considerations": [
    "List of important factors to consider",
    "Technical constraints",
    "Business requirements"
  ],
  "proposed_approach": {{
    "high_level_architecture": "Description of the proposed architecture",
    "key_components": ["Component 1", "Component 2"],
    "integration_strategy": "How systems will integrate"
  }},
  "questions_for_clarification": [
    "Questions that would help refine the solution"
  ],
  "areas_for_specialist_review": {{
    "performance": "NFR and performance considerations",
    "security": "Security aspects to review",
    "integration": "Integration points to validate"
  }},
  "risks_and_mitigation": [
    {{"risk": "Potential risk", "mitigation": "How to address it"}}
  ]
}}

Ensure your response is valid JSON and considers Salesforce best practices, governor limits, and scalability.
"""

            response = self.generate_with_safety(
                user_prompt=prompt,
                json_mode=True,
                temperature=0.7
            )

            # Validate JSON response
            try:
                json.loads(response)
            except json.JSONDecodeError as e:
                logger.warning("master_architect_invalid_json", error=str(e))
                # Wrap in valid JSON if needed
                response = json.dumps({"analysis": response})

            logger.info("master_architect_completed", response_length=len(response))

            return AgentOutput(
                content=response,
                metadata={
                    "agent": "master_architect",
                    "phase": "initial_analysis",
                    "model": self.llm_provider.get_model_name()
                },
                success=True
            )

        except Exception as e:
            logger.error("master_architect_error", error=str(e), request_preview=input_data.request[:100])
            raise AgentExecutionException(
                f"Master Architect execution failed: {str(e)}",
                details={"agent": "master_architect", "error_type": type(e).__name__}
            )

