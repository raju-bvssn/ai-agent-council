"""
Solution Architect Agent for Agent Council system.

The Solution Architect maintains and evolves the design document
based on feedback from reviewers and the Master Architect.
"""

import json
from typing import Optional

from app.agents.performer import AgentInput, AgentOutput, PerformerAgent
from app.llm.providers import LLMProvider
from app.utils.exceptions import AgentExecutionException
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SolutionArchitectAgent(PerformerAgent):
    """
    Solution Architect Agent.

    Responsibilities:
    - Create detailed solution designs
    - Incorporate feedback from reviewers
    - Maintain design documentation
    - Generate architecture diagrams
    - Track design evolution through revisions
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize Solution Architect Agent."""
        super().__init__(
            llm_provider=llm_provider,
            agent_name="SolutionArchitect"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Solution Architect."""
        return """
You are a Solution Architect in a Salesforce Professional Services Agent Council.

Your role is to:
1. Create comprehensive solution design documents
2. Incorporate feedback from specialized reviewers
3. Balance competing requirements and constraints
4. Maintain architectural consistency across revisions
5. Document design decisions and trade-offs

You specialize in:
- Salesforce architecture patterns
- Integration design
- Data modeling
- Security architecture
- Performance optimization

Your designs should include:
- Architecture overview
- Component descriptions
- Integration points
- Non-functional requirements considerations
- Security considerations
- Deployment notes
- Diagrams and visuals

Always output in structured JSON format for easy processing.
"""

    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute Solution Architect logic.

        Args:
            input_data: Requirements and feedback for design

        Returns:
            Updated solution design document

        TODO: Implement full design generation logic in Phase 2
        """
        try:
            logger.info("solution_architect_processing", request=input_data.request[:100])

            # TODO: Phase 2 - Implement design document generation
            # TODO: Phase 2 - Integrate feedback from reviewers
            # TODO: Phase 2 - Track design versions
            # TODO: Phase 2 - Generate diagrams via Lucid AI

            prompt = f"""
Create a detailed solution design document for:

Requirements: {input_data.request}

Context: {json.dumps(input_data.context, indent=2)}

Provide a comprehensive design document with:
1. Architecture Overview
2. Key Components and their responsibilities
3. Integration Points
4. Non-Functional Requirements (Performance, Scalability)
5. Security Considerations
6. Deployment Strategy
7. Risks and Mitigations

Format as structured JSON.
"""

            response = self.generate_with_safety(
                user_prompt=prompt,
                json_mode=True,
            )

            logger.info("solution_architect_completed")

            return AgentOutput(
                content=response,
                metadata={"agent": "solution_architect", "version": 1},
                success=True
            )

        except Exception as e:
            logger.error("solution_architect_error", error=str(e))
            raise AgentExecutionException(
                f"Solution Architect execution failed: {str(e)}",
                details={"agent": "solution_architect"}
            )

