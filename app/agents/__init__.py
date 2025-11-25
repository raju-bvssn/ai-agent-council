"""
Agent package for Agent Council system.

Provides:
- Base agent classes (Performer, Critic)
- Specialized agent implementations
- Agent factory for instantiation
"""

from app.agents.critic import CriticAgent, CriticInput, CriticOutput
from app.agents.factory import AgentFactory
from app.agents.faq_agent import FAQAgent
from app.agents.master_agent import MasterArchitectAgent
from app.agents.performer import AgentInput, AgentOutput, PerformerAgent
from app.agents.reviewer_agent import (
    IntegrationReviewer,
    NFRPerformanceReviewer,
    SecurityReviewer,
)
from app.agents.solution_architect_agent import SolutionArchitectAgent

__all__ = [
    # Base classes
    "PerformerAgent",
    "AgentInput",
    "AgentOutput",
    "CriticAgent",
    "CriticInput",
    "CriticOutput",
    # Concrete agents
    "MasterArchitectAgent",
    "SolutionArchitectAgent",
    "NFRPerformanceReviewer",
    "SecurityReviewer",
    "IntegrationReviewer",
    "FAQAgent",
    # Factory
    "AgentFactory",
]

