"""
Solution Architect Agent for Agent Council system.

The Solution Architect maintains and evolves the design document
based on feedback from reviewers and the Master Architect.
"""

import asyncio
import json
from typing import List, Optional

from app.agents.performer import AgentInput, AgentOutput, PerformerAgent
from app.llm.providers import LLMProvider
from app.tools import get_tool
from app.tools.schemas import ToolResult
from app.utils.exceptions import AgentExecutionException
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SolutionArchitectAgent(PerformerAgent):
    """
    Solution Architect Agent with tool integration.

    Responsibilities:
    - Create detailed solution designs
    - Incorporate feedback from reviewers
    - Maintain design documentation
    - Generate architecture diagrams (via Lucid AI)
    - Use Vibes for MuleSoft best practices
    - Use MCP Server for platform metadata
    - Track design evolution through revisions
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        allowed_tools: Optional[List[str]] = None
    ):
        """
        Initialize Solution Architect Agent.
        
        Args:
            llm_provider: LLM provider for generation
            allowed_tools: List of tool names this agent can use
        """
        super().__init__(
            llm_provider=llm_provider,
            agent_name="SolutionArchitect"
        )
        self.allowed_tools = allowed_tools or ["gemini", "lucid", "vibes"]

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

    async def _invoke_tools(self, context: dict) -> List[ToolResult]:
        """
        Invoke available tools to augment design process.
        
        Args:
            context: Design context and requirements
            
        Returns:
            List of tool results
        """
        tool_results = []
        
        # Use Vibes for MuleSoft pattern recommendations if available
        if "vibes" in self.allowed_tools:
            try:
                vibes_tool = get_tool("vibes")
                description = context.get("requirements", "") or context.get("request", "")
                
                result = await vibes_tool.execute(
                    operation="recommend_patterns",
                    parameters={"description": description}
                )
                tool_results.append(result)
                logger.info("solution_architect_vibes_invoked", success=result.success)
                
            except Exception as e:
                logger.warning("solution_architect_vibes_failed", error=str(e))
        
        # Use MCP Server for platform context if available
        if "mcp" in self.allowed_tools:
            try:
                mcp_tool = get_tool("mcp")
                
                # Get environment info
                env_result = await mcp_tool.execute(
                    operation="get_environment_info",
                    parameters={"env_id": context.get("env_id", "prod-env-001")}
                )
                tool_results.append(env_result)
                
                # Get policy list
                policy_result = await mcp_tool.execute(
                    operation="list_policies",
                    parameters={"env_id": context.get("env_id", "prod-env-001")}
                )
                tool_results.append(policy_result)
                
                logger.info("solution_architect_mcp_invoked", results=2)
                
            except Exception as e:
                logger.warning("solution_architect_mcp_failed", error=str(e))
        
        # Use Lucid for diagram generation if available
        if "lucid" in self.allowed_tools and context.get("design_description"):
            try:
                lucid_tool = get_tool("lucid")
                
                diagram_result = await lucid_tool.execute(
                    operation="generate_architecture",
                    parameters={"description": context["design_description"]}
                )
                tool_results.append(diagram_result)
                logger.info("solution_architect_lucid_invoked", success=diagram_result.success)
                
            except Exception as e:
                logger.warning("solution_architect_lucid_failed", error=str(e))
        
        return tool_results

    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute Solution Architect logic with tool augmentation.

        Args:
            input_data: Requirements and feedback for design

        Returns:
            Updated solution design document with tool results
        """
        try:
            logger.info("solution_architect_processing", request=input_data.request[:100])
            
            # Invoke tools asynchronously
            tool_results = asyncio.run(self._invoke_tools({
                "requirements": input_data.request,
                "request": input_data.request,
                "env_id": input_data.context.get("env_id") if input_data.context else None,
                "design_description": input_data.context.get("design_description") if input_data.context else None
            }))

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
            
            # Format tool results for context
            tool_context = ""
            if tool_results:
                tool_context = "\n\n**Tool-Augmented Insights:**\n"
                for result in tool_results:
                    if result.success:
                        tool_context += f"\n- **{result.tool_name}**: {result.summary}\n"
                        if result.details:
                            tool_context += f"  Details: {json.dumps(result.details, indent=2)[:500]}...\n"

            prompt = f"""
Create a comprehensive Salesforce solution design document.

**Requirements:**
{input_data.request}

**Context:**
{context_str}
{revision_context}
{tool_context}

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

            logger.info("solution_architect_completed", version=version, is_revision=is_revision, tools_used=len(tool_results))

            return AgentOutput(
                content=response,
                metadata={
                    "agent": "solution_architect",
                    "version": version,
                    "is_revision": is_revision,
                    "model": self.llm_provider.get_model_name(),
                    "tools_used": [r.tool_name for r in tool_results],
                    "tool_results": [r.dict() for r in tool_results]
                },
                success=True
            )

        except Exception as e:
            logger.error("solution_architect_error", error=str(e))
            raise AgentExecutionException(
                f"Solution Architect execution failed: {str(e)}",
                details={"agent": "solution_architect", "error_type": type(e).__name__}
            )

