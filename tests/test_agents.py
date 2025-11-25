"""
Tests for agent modules.

TODO: Phase 2 - Implement comprehensive agent tests with mocks
"""

import pytest
from unittest.mock import Mock

from app.agents.factory import AgentFactory
from app.agents.performer import AgentInput
from app.graph.state_models import AgentRole
from app.utils.exceptions import ConfigurationException


def test_agent_factory():
    """Test agent factory creation."""
    # Create master architect
    master = AgentFactory.create_agent(AgentRole.MASTER)
    assert master is not None
    assert master.agent_name == "MasterArchitect"

    # Create solution architect
    solution = AgentFactory.create_agent(AgentRole.SOLUTION_ARCHITECT)
    assert solution is not None

    # Create all reviewers
    reviewers = AgentFactory.create_all_reviewers()
    assert len(reviewers) >= 3  # At least NFR, Security, Integration


def test_master_architect_input():
    """Test agent input validation."""
    input_data = AgentInput(
        request="Design a customer portal",
        context={"industry": "healthcare"}
    )
    assert input_data.request == "Design a customer portal"
    assert input_data.context["industry"] == "healthcare"


# TODO: Phase 2 - Add more tests:
# - Mock LLM provider for agent execution
# - Test agent run() methods
# - Test reviewer logic
# - Test FAQ generation
# - Test error handling
# - Test safety wrapper integration

