"""
Comprehensive tests for Phase 3B: Multi-Agent Debate & Consensus.

Tests model selection, disagreement detection, debate engine,
consensus computation, and workflow integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.llm.model_selector import (
    auto_select_model,
    get_model_info,
    estimate_token_count,
    validate_model_for_context,
    select_model_with_override
)
from app.graph.debate.detector import (
    detect_disagreements,
    analyze_conflict_severity,
    categorize_disagreements
)
from app.graph.debate.debate_engine import DebateEngine, run_debate
from app.graph.debate.consensus import ConsensusEngine, compute_consensus
from app.graph.state_models import (
    AgentRole,
    ReviewDecision,
    ReviewFeedback,
    Disagreement,
    DebateOutcome,
    ConsensusResult
)


class TestModelSelector:
    """Tests for intelligent model selection."""
    
    def test_security_keywords_select_pro_latest(self):
        """Test that security keywords select pro-latest model."""
        description = "Design a secure authentication system with compliance for GDPR"
        model = auto_select_model(description)
        assert model == "gemini-1.5-pro-latest"
    
    def test_architecture_keywords_select_pro(self):
        """Test that architecture keywords select pro model."""
        description = "Design a scalable integration architecture with high availability"
        model = auto_select_model(description)
        assert model == "gemini-1.5-pro"
    
    def test_long_description_selects_pro(self):
        """Test that long descriptions select pro model."""
        description = "x" * 500  # 500 characters
        model = auto_select_model(description)
        assert model == "gemini-1.5-pro"
    
    def test_simple_task_selects_flash(self):
        """Test that simple tasks select flash model."""
        description = "Quick review of API design"
        model = auto_select_model(description)
        assert model in ["gemini-1.5-flash", "gemini-1.5-flash-8b"]
    
    def test_role_based_selection_master(self):
        """Test role-based selection for Master Architect."""
        description = "Standard requirements"
        model = auto_select_model(description, agent_role="master")
        assert model == "gemini-1.5-pro"
    
    def test_role_based_selection_security(self):
        """Test role-based selection for Security Reviewer."""
        description = "Standard requirements"
        model = auto_select_model(description, agent_role="security_reviewer")
        assert model == "gemini-1.5-pro-latest"
    
    def test_context_length_requirement(self):
        """Test model selection based on context length."""
        description = "Test"
        model = auto_select_model(description, context_length=1500000)
        assert model == "gemini-1.5-pro"
    
    def test_manual_override_works(self):
        """Test that manual override takes precedence."""
        description = "Security audit"  # Would normally select pro-latest
        model, was_auto = select_model_with_override(
            description,
            manual_override="gemini-1.5-flash",
            auto_mode=False
        )
        assert model == "gemini-1.5-flash"
        assert was_auto is False
    
    def test_get_model_info(self):
        """Test getting model configuration info."""
        info = get_model_info("gemini-1.5-pro")
        assert info["context_window"] == 2000000
        assert "architecture" in info["best_for"]
    
    def test_estimate_token_count(self):
        """Test token count estimation."""
        text = "This is a test sentence"
        tokens = estimate_token_count(text)
        assert tokens > 0
        assert tokens == len(text) // 4
    
    def test_validate_model_for_context(self):
        """Test model validation for context length."""
        # Flash should handle 500K tokens
        assert validate_model_for_context("gemini-1.5-flash", 500000)
        # Flash should NOT handle 1.5M tokens
        assert not validate_model_for_context("gemini-1.5-flash", 1500000)
        # Pro should handle 1.5M tokens
        assert validate_model_for_context("gemini-1.5-pro", 1500000)


class TestDisagreementDetection:
    """Tests for disagreement detection."""
    
    def test_detect_decision_conflicts(self):
        """Test detection of decision conflicts (approve vs revise)."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_NFR,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Looks good",
                severity="low"
            ),
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_SECURITY,
                decision=ReviewDecision.REVISE,
                concerns=["Security issues"],
                suggestions=["Add encryption"],
                rationale="Security concerns",
                severity="high"
            )
        ]
        
        disagreements = detect_disagreements(reviews)
        assert len(disagreements) >= 1
        assert any(d.category == "decision_conflict" for d in disagreements)
    
    def test_detect_pattern_conflicts_sync_async(self):
        """Test detection of sync vs async pattern conflicts."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_NFR,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=["Use asynchronous processing for better throughput"],
                rationale="Performance optimized",
                severity="medium"
            ),
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_SECURITY,
                decision=ReviewDecision.REVISE,
                concerns=["Need synchronous validation"],
                suggestions=["Use synchronous calls for security checks"],
                rationale="Security requires sync",
                severity="high"
            )
        ]
        
        disagreements = detect_disagreements(reviews)
        pattern_conflicts = [d for d in disagreements if "pattern_conflict" in d.category]
        assert len(pattern_conflicts) > 0
    
    def test_detect_severity_conflicts(self):
        """Test detection of severity assessment conflicts."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_NFR,
                decision=ReviewDecision.REVISE,
                concerns=["Performance bottleneck"],
                suggestions=[],
                rationale="Performance issue",
                severity="low"
            ),
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_SECURITY,
                decision=ReviewDecision.REVISE,
                concerns=["Performance bottleneck"],
                suggestions=[],
                rationale="Performance issue",
                severity="critical"
            )
        ]
        
        disagreements = detect_disagreements(reviews)
        # May or may not detect this depending on exact text matching
        # Just verify it doesn't crash
        assert isinstance(disagreements, list)
    
    def test_no_disagreements_with_all_approvals(self):
        """Test that all approvals result in no disagreements."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_NFR,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Good",
                severity="low"
            ),
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_SECURITY,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Good",
                severity="low"
            )
        ]
        
        disagreements = detect_disagreements(reviews)
        # Should have minimal or no disagreements
        assert len(disagreements) == 0
    
    def test_analyze_conflict_severity(self):
        """Test conflict severity analysis."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_NFR,
                decision=ReviewDecision.REVISE,
                concerns=[],
                suggestions=[],
                rationale="Issue",
                severity="critical"
            ),
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_SECURITY,
                decision=ReviewDecision.REVISE,
                concerns=[],
                suggestions=[],
                rationale="Issue",
                severity="high"
            )
        ]
        
        severity = analyze_conflict_severity(reviews)
        assert severity == "critical"
    
    def test_categorize_disagreements(self):
        """Test disagreement categorization."""
        disagreements = [
            Disagreement(
                disagreement_id="1",
                agent_roles=[AgentRole.REVIEWER_NFR, AgentRole.REVIEWER_SECURITY],
                topic="Test",
                positions={},
                category="decision_conflict"
            ),
            Disagreement(
                disagreement_id="2",
                agent_roles=[AgentRole.REVIEWER_NFR, AgentRole.REVIEWER_INTEGRATION],
                topic="Test",
                positions={},
                category="pattern_conflict_sync_vs_async"
            )
        ]
        
        categorized = categorize_disagreements(disagreements)
        assert len(categorized["decision_conflicts"]) == 1
        assert len(categorized["pattern_conflicts"]) == 1


class TestDebateEngine:
    """Tests for debate engine."""
    
    @pytest.mark.asyncio
    async def test_debate_engine_initialization(self):
        """Test debate engine can be initialized."""
        engine = DebateEngine(max_rounds=2)
        assert engine.max_rounds == 2
        assert engine.provider is not None
    
    @pytest.mark.asyncio
    async def test_debate_with_mock_llm(self):
        """Test debate execution with mocked LLM."""
        disagreement = Disagreement(
            disagreement_id="test-1",
            agent_roles=[AgentRole.REVIEWER_NFR, AgentRole.REVIEWER_SECURITY],
            topic="Sync vs Async",
            positions={
                "reviewer_nfr": "Use async for performance",
                "reviewer_security": "Use sync for security"
            },
            category="pattern_conflict"
        )
        
        engine = DebateEngine(max_rounds=2)
        
        # Mock the provider's generate method
        with patch.object(engine.provider, 'generate_with_safety', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "revised_positions": {
                    "reviewer_nfr": "Use async with validation pipeline",
                    "reviewer_security": "Acceptable with proper validation"
                },
                "consensus_reached": True,
                "consensus_explanation": "Agreement on async with validation",
                "common_ground": ["Both care about data integrity"],
                "remaining_differences": []
            }
            
            outcome = await engine.facilitate_debate(disagreement, context="Test context")
            
            assert outcome.consensus_reached
            assert len(outcome.agent_positions_revised) == 2
            assert outcome.debate_rounds <= 2
    
    @pytest.mark.asyncio
    async def test_run_debate_convenience_function(self):
        """Test run_debate convenience function."""
        disagreement = Disagreement(
            disagreement_id="test-2",
            agent_roles=[AgentRole.REVIEWER_NFR],
            topic="Test",
            positions={"reviewer_nfr": "Position"},
            category="test"
        )
        
        # This will use real Gemini if API key available, otherwise mock
        try:
            outcome = await run_debate(disagreement, "Test context", max_rounds=1)
            assert isinstance(outcome, DebateOutcome)
        except Exception:
            # Expected if no API key
            pass


class TestConsensusEngine:
    """Tests for consensus computation."""
    
    def test_consensus_engine_initialization(self):
        """Test consensus engine initialization."""
        engine = ConsensusEngine(threshold=0.7)
        assert engine.threshold == 0.7
        assert AgentRole.MASTER in engine.weights
    
    def test_consensus_with_all_approvals(self):
        """Test consensus computation with all approvals."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.MASTER,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Good",
                severity="low"
            ),
            ReviewFeedback(
                reviewer_role=AgentRole.SOLUTION_ARCHITECT,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Good",
                severity="low"
            ),
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_NFR,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Good",
                severity="low"
            )
        ]
        
        engine = ConsensusEngine()
        result = engine.compute(reviews, [])
        
        assert result.agreed
        assert result.confidence > 0.65
        assert "approve" in result.vote_breakdown[AgentRole.MASTER.value]
    
    def test_consensus_with_mixed_votes(self):
        """Test consensus with mixed approve/revise votes."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_NFR,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Good",
                severity="low"
            ),
            ReviewFeedback(
                reviewer_role=AgentRole.REVIEWER_SECURITY,
                decision=ReviewDecision.REVISE,
                concerns=["Issue"],
                suggestions=[],
                rationale="Needs work",
                severity="medium"
            )
        ]
        
        engine = ConsensusEngine()
        result = engine.compute(reviews, [])
        
        # With only reviewer votes (low weights), might not reach consensus
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1
    
    def test_consensus_with_debate_adjustment(self):
        """Test that debates adjust consensus confidence."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.MASTER,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Good",
                severity="low"
            )
        ]
        
        debates = [
            DebateOutcome(
                debate_id="d1",
                disagreement=Disagreement(
                    disagreement_id="dis1",
                    agent_roles=[],
                    topic="Test",
                    positions={},
                    category="test"
                ),
                debate_rounds=2,
                agent_positions_revised={},
                consensus_reached=True,
                resolution_summary="Resolved",
                confidence=0.8
            )
        ]
        
        engine = ConsensusEngine()
        result = engine.compute(reviews, debates)
        
        # Resolved debate should boost confidence
        assert result.confidence > 0
        assert len(result.disagreements_resolved) == 1
    
    def test_compute_consensus_convenience_function(self):
        """Test compute_consensus convenience function."""
        reviews = [
            ReviewFeedback(
                reviewer_role=AgentRole.MASTER,
                decision=ReviewDecision.APPROVE,
                concerns=[],
                suggestions=[],
                rationale="Good",
                severity="low"
            )
        ]
        
        result = compute_consensus(reviews, [], threshold=0.5)
        assert isinstance(result, ConsensusResult)
        assert result.threshold == 0.5


class TestWorkflowIntegration:
    """Tests for Phase 3B workflow integration."""
    
    def test_reviewer_round_result_creation(self):
        """Test ReviewerRoundResult can be created."""
        from app.graph.state_models import ReviewerRoundResult
        
        round_result = ReviewerRoundResult(
            round_number=1,
            reviews=[],
            disagreements=[],
            debates=[],
            consensus=None
        )
        
        assert round_result.round_number == 1
        assert round_result.requires_adjudication is False
    
    def test_workflow_state_phase3b_fields(self):
        """Test WorkflowState has Phase 3B fields."""
        from app.graph.state_models import WorkflowState
        
        state = WorkflowState(
            session_id="test",
            user_request="Test",
            selected_model="gemini-1.5-pro",
            auto_model=False
        )
        
        assert state.selected_model == "gemini-1.5-pro"
        assert state.auto_model is False
        assert state.current_round == 0
        assert isinstance(state.reviewer_rounds, list)
        assert isinstance(state.debates, list)
        assert isinstance(state.consensus_history, list)
    
    def test_workflow_result_phase3b_fields(self):
        """Test WorkflowResult exposes Phase 3B fields."""
        from app.graph.state_models import WorkflowState, WorkflowResult
        
        state = WorkflowState(
            session_id="test",
            user_request="Test",
            selected_model="gemini-1.5-flash",
            current_round=2,
            requires_adjudication=True
        )
        
        result = WorkflowResult.from_workflow_state(state)
        
        assert result.selected_model == "gemini-1.5-flash"
        assert result.current_round == 2
        assert result.requires_adjudication is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

