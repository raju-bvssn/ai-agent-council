"""
Agent factory for Agent Council system.

Implements Factory Pattern for agent instantiation.
"""

from typing import Optional

from app.agents.faq_agent import FAQAgent
from app.agents.master_agent import MasterArchitectAgent
from app.agents.reviewer_agent import (
    IntegrationReviewer,
    NFRPerformanceReviewer,
    SecurityReviewer,
)
from app.agents.solution_architect_agent import SolutionArchitectAgent
from app.graph.state_models import AgentRole
from app.llm.providers import LLMProvider
from app.utils.exceptions import ConfigurationException
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """
    Factory for creating agent instances.

    Implements Factory Pattern and Dependency Injection.
    """

    @staticmethod
    def create_agent(
        agent_role: AgentRole,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Create agent instance by role.

        Args:
            agent_role: Role of the agent to create
            llm_provider: LLM provider instance (optional)

        Returns:
            Agent instance

        Raises:
            ConfigurationException: If agent role not supported
        """
        logger.info("creating_agent", role=agent_role.value)

        if agent_role == AgentRole.MASTER:
            return MasterArchitectAgent(llm_provider=llm_provider)

        elif agent_role == AgentRole.SOLUTION_ARCHITECT:
            return SolutionArchitectAgent(llm_provider=llm_provider)

        elif agent_role == AgentRole.REVIEWER_NFR:
            return NFRPerformanceReviewer(llm_provider=llm_provider)

        elif agent_role == AgentRole.REVIEWER_SECURITY:
            return SecurityReviewer(llm_provider=llm_provider)

        elif agent_role == AgentRole.REVIEWER_INTEGRATION:
            return IntegrationReviewer(llm_provider=llm_provider)

        elif agent_role == AgentRole.FAQ:
            return FAQAgent(llm_provider=llm_provider)

        # TODO: Phase 2 - Add DomainExpertReviewer
        # TODO: Phase 2 - Add OperationsReviewer

        else:
            raise ConfigurationException(
                f"Unsupported agent role: {agent_role}",
                details={"role": agent_role.value}
            )

    @staticmethod
    def create_all_reviewers(
        llm_provider: Optional[LLMProvider] = None,
    ) -> dict[AgentRole, any]:
        """
        Create all reviewer agents.

        Args:
            llm_provider: LLM provider instance (optional)

        Returns:
            Dictionary mapping AgentRole to agent instances
        """
        reviewer_roles = [
            AgentRole.REVIEWER_NFR,
            AgentRole.REVIEWER_SECURITY,
            AgentRole.REVIEWER_INTEGRATION,
            # TODO: Phase 2 - Add more reviewers
        ]

        return {
            role: AgentFactory.create_agent(role, llm_provider)
            for role in reviewer_roles
        }

