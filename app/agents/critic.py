"""
Critic base class for Agent Council system.

Critics are agents that evaluate and provide feedback on content.
Base class implements common functionality for all critic agents.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel

from app.graph.state_models import ReviewDecision
from app.llm.providers import LLMProvider
from app.llm.safety import get_safety_wrapper
from app.llm.factory import get_llm_provider
from app.tools import get_tool
from app.tools.schemas import ToolResult
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CriticInput(BaseModel):
    """Input model for critic agents."""
    content_to_review: str
    context: dict = {}


class CriticOutput(BaseModel):
    """Output model for critic agents with tool support."""
    decision: ReviewDecision
    concerns: list[str] = []
    suggestions: list[str] = []
    rationale: str
    severity: str = "medium"
    success: bool = True
    error: Optional[str] = None
    tool_results: list[dict] = []  # Results from tool invocations


class CriticAgent(ABC):
    """
    Base class for all critic/reviewer agents with tool integration.

    Implements:
    - Constructor injection for dependencies
    - Common review patterns
    - Structured feedback generation
    - Safety wrapper integration
    - Tool invocation for augmented reviews
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        agent_name: str = "CriticAgent",
        allowed_tools: Optional[List[str]] = None
    ):
        """
        Initialize critic agent.

        Args:
            llm_provider: LLM provider instance (creates default if None)
            agent_name: Name of the agent for logging
            allowed_tools: List of tool names this agent can use
        """
        self.llm_provider = llm_provider or get_llm_provider()
        self.agent_name = agent_name
        self.safety_wrapper = get_safety_wrapper(strict_mode=False)
        self.allowed_tools = allowed_tools or []
        logger.info(f"{agent_name}_initialized", model=self.llm_provider.get_model_name(), tools=self.allowed_tools)
    
    async def _invoke_tools_for_review(self, content: str, context: dict) -> List[ToolResult]:
        """
        Invoke available tools to augment the review process.
        
        Args:
            content: Content being reviewed
            context: Review context
            
        Returns:
            List of tool results
        """
        tool_results = []
        
        # Subclasses can override this to provide specialized tool invocation
        # Default: no tools invoked
        
        return tool_results

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this critic agent.

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def run(self, input_data: CriticInput) -> CriticOutput:
        """
        Execute the critic's review logic.

        Args:
            input_data: Content and context to review

        Returns:
            Critic output with structured feedback
        """
        pass

    def generate_review(
        self,
        content: str,
        review_criteria: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate review using LLM with safety checks.

        Args:
            content: Content to review
            review_criteria: Specific criteria for this review
            system_prompt: System prompt override

        Returns:
            Generated review text
        """
        system_prompt = system_prompt or self.get_system_prompt()

        user_prompt = f"""
Review the following content according to these criteria:

{review_criteria}

Content to Review:
{content}

Provide structured feedback in JSON format with:
- decision: "approve", "reject", "revise", or "escalate"
- concerns: list of specific issues found
- suggestions: list of actionable improvements
- rationale: explanation of your decision
- severity: "low", "medium", "high", or "critical"
"""

        result = self.safety_wrapper.wrap_llm_call(
            system_prompt=system_prompt,
            user_input=user_prompt,
            llm_function=lambda **kwargs: self.llm_provider.generate(
                prompt=kwargs["user_input"],
                system_prompt=kwargs["system_prompt"],
                json_mode=True,
            )
        )

        return result

