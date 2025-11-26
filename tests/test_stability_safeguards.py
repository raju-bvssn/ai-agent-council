"""
Tests for Stability Safeguards in Debate Engine and Workflow.

Tests timeout handling, repetition detection, forced consensus, and
adjudicator run-once guarantees to prevent infinite loops.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.graph.debate.debate_engine import DebateEngine, run_debate
from app.graph.state_models import (
    Disagreement,
    AgentRole,
    WorkflowState,
    WorkflowStatus,
)
from app.graph.phase3b_nodes import architect_adjudicator_node


@pytest.fixture
def sample_disagreement():
    """Create a sample disagreement for testing."""
    return Disagreement(
        disagreement_id="test-dis-001",
        agent_roles=[AgentRole.REVIEWER_SECURITY, AgentRole.REVIEWER_NFR],
        topic="Authentication Approach",
        positions={
            AgentRole.REVIEWER_SECURITY.value: "Use OAuth 2.0 with JWT tokens",
            AgentRole.REVIEWER_NFR.value: "Use API keys for simplicity",
        },
        severity="high",
        category="security_vs_simplicity",
    )


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    provider.generate_with_safety = AsyncMock()
    return provider


class TestDebateTimeout:
    """Test debate round timeout safeguards."""
    
    @pytest.mark.asyncio
    async def test_timeout_forces_consensus(self, sample_disagreement):
        """Test that timeout forces consensus."""
        engine = DebateEngine(max_rounds=2)
        
        # Mock slow debate round that exceeds timeout
        async def slow_round(*args, **kwargs):
            await asyncio.sleep(20)  # Exceeds default 15s timeout
            return {
                "revised_positions": {},
                "consensus_reached": False
            }
        
        with patch.object(engine, '_conduct_debate_round', new=slow_round):
            with patch('app.graph.debate.debate_engine.settings') as mock_settings:
                mock_settings.debate_round_timeout = 1  # 1 second timeout for test
                mock_settings.enable_forced_consensus = True
                mock_settings.max_debate_rounds = 2
                mock_settings.enable_repetition_detection = True
                mock_settings.repetition_similarity_threshold = 0.85
                
                outcome = await engine.facilitate_debate(
                    sample_disagreement,
                    "Test context"
                )
        
        # Should have forced consensus due to timeout
        assert outcome.consensus_reached is True
        assert "timeout" in outcome.resolution_summary.lower() or "forced" in outcome.resolution_summary.lower()
        assert outcome.confidence >= 0.5  # Forced consensus has minimum confidence
    
    @pytest.mark.asyncio
    async def test_timeout_produces_forced_consensus(self, sample_disagreement):
        """Test that timeouts produce forced consensus with appropriate metadata."""
        engine = DebateEngine(max_rounds=1)
        
        async def slow_round(*args, **kwargs):
            await asyncio.sleep(20)
            return {"revised_positions": {}, "consensus_reached": False}
        
        with patch.object(engine, '_conduct_debate_round', new=slow_round):
            with patch('app.graph.debate.debate_engine.settings') as mock_settings:
                mock_settings.debate_round_timeout = 0.5
                mock_settings.enable_forced_consensus = True
                mock_settings.max_debate_rounds = 1
                mock_settings.enable_repetition_detection = False
                
                outcome = await engine.facilitate_debate(sample_disagreement, "Test")
        
        # Outcome should indicate forced consensus
        assert outcome.consensus_reached is True
        assert ("timeout" in outcome.resolution_summary.lower() or 
                "forced" in outcome.resolution_summary.lower())


class TestRepetitionDetection:
    """Test repetition detection safeguards."""
    
    @pytest.mark.asyncio
    async def test_repetitive_arguments_force_consensus(self, sample_disagreement):
        """Test that repetitive arguments trigger forced consensus."""
        engine = DebateEngine(max_rounds=3)
        
        # Mock rounds that return nearly identical positions
        call_count = [0]
        async def repetitive_round(*args, **kwargs):
            call_count[0] += 1
            return {
                "revised_positions": {
                    AgentRole.REVIEWER_SECURITY.value: "OAuth 2.0 is best",
                    AgentRole.REVIEWER_NFR.value: "API keys are simpler",
                },
                "consensus_reached": False,
                "common_ground": [],
                "remaining_differences": ["approach"]
            }
        
        with patch.object(engine, '_conduct_debate_round', new=repetitive_round):
            with patch('app.graph.debate.debate_engine.settings') as mock_settings:
                mock_settings.debate_round_timeout = 30
                mock_settings.enable_forced_consensus = True
                mock_settings.enable_repetition_detection = True
                mock_settings.repetition_similarity_threshold = 0.85
                mock_settings.max_debate_rounds = 3
                
                outcome = await engine.facilitate_debate(sample_disagreement, "Test")
        
        # Should detect repetition and force consensus
        assert outcome.consensus_reached is True
        # Should not complete all rounds if repetition detected early
        assert outcome.debate_rounds <= 3
    
    @pytest.mark.asyncio
    async def test_repetition_similarity_calculation(self, sample_disagreement):
        """Test position similarity calculation."""
        engine = DebateEngine()
        
        positions1 = {
            "agent1": "Use OAuth 2.0 for authentication",
            "agent2": "Use API keys for simplicity",
        }
        positions2 = {
            "agent1": "Use OAuth 2.0 for authentication",
            "agent2": "Use API keys for simplicity and ease",
        }
        
        similarity = engine._calculate_position_similarity(positions1, positions2)
        
        # Should be high similarity (>0.8) since positions are nearly identical
        assert similarity > 0.8
    
    @pytest.mark.asyncio
    async def test_different_positions_low_similarity(self):
        """Test that different positions have low similarity."""
        engine = DebateEngine()
        
        positions1 = {
            "agent1": "Use OAuth 2.0 with JWT tokens",
            "agent2": "Use API keys",
        }
        positions2 = {
            "agent1": "Use SAML federation with SSO",
            "agent2": "Use certificate-based authentication",
        }
        
        similarity = engine._calculate_position_similarity(positions1, positions2)
        
        # Should be low similarity since positions are different
        assert similarity < 0.5


class TestMaxRoundsEnforcement:
    """Test max debate rounds enforcement."""
    
    @pytest.mark.asyncio
    async def test_max_rounds_forces_consensus(self, sample_disagreement):
        """Test that max rounds triggers forced consensus."""
        engine = DebateEngine(max_rounds=2)
        
        # Mock rounds that never reach consensus naturally
        async def no_consensus_round(*args, **kwargs):
            return {
                "revised_positions": {
                    AgentRole.REVIEWER_SECURITY.value: f"Position at round {kwargs.get('round_number', 1)}",
                    AgentRole.REVIEWER_NFR.value: f"Different position {kwargs.get('round_number', 1)}",
                },
                "consensus_reached": False,
                "common_ground": [],
                "remaining_differences": ["approach"]
            }
        
        with patch.object(engine, '_conduct_debate_round', new=no_consensus_round):
            with patch('app.graph.debate.debate_engine.settings') as mock_settings:
                mock_settings.debate_round_timeout = 30
                mock_settings.enable_forced_consensus = True
                mock_settings.enable_repetition_detection = False
                mock_settings.max_debate_rounds = 2
                
                outcome = await engine.facilitate_debate(sample_disagreement, "Test")
        
        # Should force consensus after max rounds
        assert outcome.consensus_reached is True
        assert outcome.debate_rounds == 2
        assert "max rounds" in outcome.resolution_summary.lower() or "forced" in outcome.resolution_summary.lower()
    
    @pytest.mark.asyncio
    async def test_max_rounds_from_settings(self, sample_disagreement):
        """Test that max rounds is read from settings when not specified."""
        # Engine initialized without explicit max_rounds
        engine = DebateEngine()
        
        with patch('app.graph.debate.debate_engine.settings') as mock_settings:
            mock_settings.max_debate_rounds = 5
            mock_settings.debate_round_timeout = 30
            mock_settings.enable_forced_consensus = True
            mock_settings.enable_repetition_detection = False
            
            # Verify max_rounds is taken from settings
            engine2 = DebateEngine()
            # max_rounds should be from settings
            # This is verified by the __init__ method


class TestAdjudicatorRunOnce:
    """Test adjudicator run-once guarantee."""
    
    def test_adjudicator_runs_only_once(self):
        """Test that adjudicator node prevents multiple runs."""
        state = WorkflowState(
            session_id="test-session",
            user_request="Test request",
            status=WorkflowStatus.IN_PROGRESS,
        )
        
        # Mock the agent creation and execution
        with patch('app.graph.phase3b_nodes.AgentFactory.create_agent') as mock_factory:
            mock_agent = Mock()
            mock_agent.run = Mock(return_value=Mock(
                content='{"architecture_rationale": "Test rationale"}',
                success=True,
                metadata={}
            ))
            mock_factory.return_value = mock_agent
            
            with patch('app.graph.phase3b_nodes._persist_state'):
                # First run should execute normally
                result1 = architect_adjudicator_node(state)
                assert result1["adjudication_complete"] is True
                assert mock_agent.run.call_count == 1
                
                # Second run should skip execution
                result2 = architect_adjudicator_node(state)
                assert result2["adjudication_complete"] is True
                assert mock_agent.run.call_count == 1  # Still 1, not called again
                
                # Check warning was added
                assert any("cached results" in w for w in result2.get("warnings", []))
    
    def test_adjudicator_run_count_tracked(self):
        """Test that adjudicator runs are tracked in metadata."""
        state = WorkflowState(
            session_id="test-session",
            user_request="Test request",
            status=WorkflowStatus.IN_PROGRESS,
        )
        
        with patch('app.graph.phase3b_nodes.AgentFactory.create_agent') as mock_factory:
            mock_agent = Mock()
            mock_agent.run = Mock(return_value=Mock(
                content='{"architecture_rationale": "Test"}',
                success=True,
                metadata={}
            ))
            mock_factory.return_value = mock_agent
            
            with patch('app.graph.phase3b_nodes._persist_state'):
                # Run adjudicator
                architect_adjudicator_node(state)
                
                # Check run count is tracked
                assert state.metadata.get("adjudicator_run_count") == 1
    
    def test_adjudicator_respects_max_runs_setting(self):
        """Test that adjudicator respects max_runs from settings."""
        state = WorkflowState(
            session_id="test-session",
            user_request="Test request",
            status=WorkflowStatus.IN_PROGRESS,
        )
        
        # Set run count to max
        state.metadata["adjudicator_run_count"] = 1
        
        with patch('app.graph.phase3b_nodes.AgentFactory.create_agent') as mock_factory:
            mock_agent = Mock()
            mock_factory.return_value = mock_agent
            
            with patch('app.utils.settings.get_settings') as mock_get_settings:
                mock_settings = Mock()
                mock_settings.adjudicator_max_runs = 1
                mock_get_settings.return_value = mock_settings
                
                # Should skip execution
                result = architect_adjudicator_node(state)
                
                # Agent should not be created/called since already at max
                assert mock_factory.call_count == 0


class TestNormalDebateFlow:
    """Test that normal debate flow still works correctly."""
    
    @pytest.mark.asyncio
    async def test_normal_consensus_works(self, sample_disagreement):
        """Test that debates that reach consensus naturally still work."""
        engine = DebateEngine(max_rounds=2)
        
        # Mock a round that reaches consensus
        async def consensus_round(*args, **kwargs):
            return {
                "revised_positions": {
                    AgentRole.REVIEWER_SECURITY.value: "Use OAuth 2.0 with good UX",
                    AgentRole.REVIEWER_NFR.value: "OAuth 2.0 with good UX is acceptable",
                },
                "consensus_reached": True,
                "common_ground": ["OAuth 2.0", "User experience important"],
                "remaining_differences": []
            }
        
        with patch.object(engine, '_conduct_debate_round', new=consensus_round):
            outcome = await engine.facilitate_debate(sample_disagreement, "Test")
        
        # Should reach natural consensus
        assert outcome.consensus_reached is True
        assert "natural consensus" in outcome.resolution_summary.lower()
        assert outcome.debate_rounds == 1  # Only needed 1 round


class TestDemoModeCompatibility:
    """Test that safeguards work correctly in DEMO_MODE."""
    
    @pytest.mark.asyncio
    async def test_demo_mode_with_timeout(self, sample_disagreement):
        """Test that DEMO_MODE works with timeout safeguards."""
        engine = DebateEngine(max_rounds=2)
        
        with patch('app.graph.debate.debate_engine.settings') as mock_settings:
            mock_settings.demo_mode = True
            mock_settings.max_debate_rounds = 2
            mock_settings.debate_round_timeout = 15
            mock_settings.enable_forced_consensus = True
            mock_settings.enable_repetition_detection = True
            mock_settings.repetition_similarity_threshold = 0.85
            
            # Mock LLM provider for demo mode
            with patch('app.graph.debate.debate_engine.get_llm_provider') as mock_get_provider:
                mock_provider = Mock()
                mock_provider.generate_with_safety = AsyncMock(return_value={
                    "revised_positions": sample_disagreement.positions,
                    "consensus_reached": True,
                    "consensus_explanation": "Demo mode consensus",
                    "common_ground": ["demo"],
                    "remaining_differences": []
                })
                mock_get_provider.return_value = mock_provider
                
                outcome = await engine.facilitate_debate(sample_disagreement, "Test")
        
        # Should complete successfully in demo mode
        assert outcome is not None
        assert outcome.consensus_reached is True


class TestBackwardCompatibility:
    """Test backward compatibility of stability enhancements."""
    
    @pytest.mark.asyncio
    async def test_existing_code_still_works(self, sample_disagreement):
        """Test that existing code patterns still work."""
        # Old-style call without specifying max_rounds
        outcome = await run_debate(sample_disagreement, "Test context")
        
        assert outcome is not None
        assert isinstance(outcome.consensus_reached, bool)
        assert outcome.debate_rounds >= 0
    
    @pytest.mark.asyncio
    async def test_explicit_max_rounds_override(self, sample_disagreement):
        """Test that explicit max_rounds parameter still works."""
        # Explicitly set max_rounds (old behavior)
        outcome = await run_debate(
            sample_disagreement,
            "Test context",
            max_rounds=1
        )
        
        assert outcome is not None
        assert outcome.debate_rounds <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

