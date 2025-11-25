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
        """
        try:
            logger.info("solution_architect_processing", request=input_data.request[:100])

            # Extract context and previous feedback
            context_str = json.dumps(input_data.context, indent=2) if input_data.context else "No context"
            
            # Check if this is a revision
            reviews = input_data.context.get("reviews", []) if input_data.context else []
            is_revision = len(reviews) > 0
            version = input_data.context.get("version", 1) if input_data.context else 1

            revision_context = ""
            if is_revision:
                revision_context = "\n\n**Previous Review Feedback:**\n"
                for review in reviews:
                    revision_context += f"\n- **{review.get('reviewer')}** ({review.get('decision')})\n"
                    if review.get('concerns'):
                        revision_context += f"  Concerns: {', '.join(review['concerns'])}\n"
                    if review.get('suggestions'):
                        revision_context += f"  Suggestions: {', '.join(review['suggestions'])}\n"

            prompt = f"""
Create a comprehensive Salesforce solution design document.

**Requirements:**
{input_data.request}

**Context:**
{context_str}
{revision_context}

**Your Task:**
Generate a detailed design document in the following JSON structure:
{{
  "title": "Solution Title",
  "version": {version},
  "description": "Executive summary of the solution",
  "architecture_overview": "Detailed architecture description with data flow",
  "components": [
    {{
      "name": "Component Name",
      "type": "Salesforce/Integration/Custom",
      "responsibility": "What this component does",
      "technology": "Apex/LWC/Flow/External",
      "interfaces": ["How it connects to other components"]
    }}
  ],
  "nfr_considerations": {{
    "performance": "Performance strategy and optimizations",
    "scalability": "How the solution scales",
    "governor_limits": "How Salesforce limits are managed",
    "caching": "Caching strategy if applicable"
  }},
  "security_considerations": {{
    "authentication": "Auth strategy",
    "authorization": "Permission and sharing model",
    "data_protection": "Encryption and data security",
    "compliance": "Regulatory compliance notes"
  }},
  "integration_points": [
    {{
      "name": "Integration Name",
      "type": "REST/SOAP/Event/Batch",
      "source": "Source system",
      "target": "Target system",
      "error_handling": "Error strategy"
    }}
  ],
  "deployment_notes": "Deployment strategy and considerations",
  "risks_and_mitigations": [
    {{"risk": "Risk description", "probability": "High/Medium/Low", "mitigation": "Mitigation strategy"}}
  ]
}}

{f"**IMPORTANT:** Address all reviewer concerns from above. This is version {version} - improve upon previous feedback." if is_revision else ""}

Ensure comprehensive coverage of Salesforce best practices, scalability patterns, and enterprise architecture principles.
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
                logger.warning("solution_architect_invalid_json", error=str(e))
                response = json.dumps({"design": response})

            logger.info("solution_architect_completed", version=version, is_revision=is_revision)

            return AgentOutput(
                content=response,
                metadata={
                    "agent": "solution_architect",
                    "version": version,
                    "is_revision": is_revision,
                    "model": self.llm_provider.get_model_name()
                },
                success=True
            )

        except Exception as e:
            logger.error("solution_architect_error", error=str(e))
            raise AgentExecutionException(
                f"Solution Architect execution failed: {str(e)}",
                details={"agent": "solution_architect", "error_type": type(e).__name__}
            )

