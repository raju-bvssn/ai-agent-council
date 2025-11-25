"""
Performer base class for Agent Council system.

Performers are agents that generate or transform content.
Base class implements common functionality for all performing agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel

from app.llm.factory import get_llm_provider
from app.llm.providers import LLMProvider
from app.llm.safety import get_safety_wrapper
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AgentInput(BaseModel):
    """Base input model for agents."""
    request: str
    context: dict[str, Any] = {}


class AgentOutput(BaseModel):
    """Base output model for agents."""
    content: str
    metadata: dict[str, Any] = {}
    success: bool = True
    error: Optional[str] = None


class PerformerAgent(ABC):
    """
    Base class for all performer agents.

    Implements:
    - Constructor injection for dependencies
    - Common LLM interaction patterns
    - Safety wrapper integration
    - Logging and error handling
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        agent_name: str = "PerformerAgent",
    ):
        """
        Initialize performer agent.

        Args:
            llm_provider: LLM provider instance (creates default if None)
            agent_name: Name of the agent for logging
        """
        self.llm_provider = llm_provider or get_llm_provider()
        self.agent_name = agent_name
        self.safety_wrapper = get_safety_wrapper(strict_mode=False)
        logger.info(f"{agent_name}_initialized", model=self.llm_provider.get_model_name())

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the agent's main logic.

        Args:
            input_data: Input data for the agent

        Returns:
            Agent output
        """
        pass

    def generate_with_safety(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate LLM response with safety checks.

        Args:
            user_prompt: User prompt
            system_prompt: System prompt (uses get_system_prompt if None)
            temperature: Temperature override
            json_mode: Force JSON output

        Returns:
            Generated text
        """
        system_prompt = system_prompt or self.get_system_prompt()

        # Use safety wrapper
        result = self.safety_wrapper.wrap_llm_call(
            system_prompt=system_prompt,
            user_input=user_prompt,
            llm_function=lambda **kwargs: self.llm_provider.generate(
                prompt=kwargs["user_input"],
                system_prompt=kwargs["system_prompt"],
                temperature=temperature,
                json_mode=json_mode,
            )
        )

        return result

