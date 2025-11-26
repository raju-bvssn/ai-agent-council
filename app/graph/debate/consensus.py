"""
Consensus engine for Agent Council.

Computes weighted consensus from reviewer feedback and debate outcomes.
Uses configurable weights for different agent roles.
"""

import uuid
from typing import List, Optional
from datetime import datetime

from app.graph.state_models import (
    ReviewFeedback,
    DebateOutcome,
    ConsensusResult,
    ReviewDecision,
    AgentRole
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Agent role weights for consensus calculation
AGENT_WEIGHTS = {
    AgentRole.MASTER: 0.25,  # Master Architect has significant weight
    AgentRole.SOLUTION_ARCHITECT: 0.25,  # Solution Architect equal to Master
    AgentRole.REVIEWER_NFR: 0.10,
    AgentRole.REVIEWER_SECURITY: 0.15,  # Security slightly higher weight
    AgentRole.REVIEWER_INTEGRATION: 0.10,
    AgentRole.REVIEWER_DOMAIN: 0.08,
    AgentRole.REVIEWER_OPS: 0.07,
    # Default weight for any other roles
    "default": 0.05
}

# Consensus threshold
DEFAULT_CONSENSUS_THRESHOLD = 0.65


class ConsensusEngine:
    """
    Engine for computing consensus from reviewer feedback.
    
    Uses weighted scoring to determine if agents agree on the design.
    """
    
    def __init__(
        self,
        weights: Optional[dict] = None,
        threshold: float = DEFAULT_CONSENSUS_THRESHOLD
    ):
        """
        Initialize consensus engine.
        
        Args:
            weights: Custom agent weights (uses defaults if None)
            threshold: Minimum confidence for consensus (0-1)
        """
        self.weights = weights or AGENT_WEIGHTS
        self.threshold = threshold
        logger.info("consensus_engine_initialized", threshold=threshold)
    
    def compute(
        self,
        reviews: List[ReviewFeedback],
        debates: List[DebateOutcome]
    ) -> ConsensusResult:
        """
        Compute consensus from reviews and debate outcomes.
        
        Args:
            reviews: Reviewer feedback
            debates: Debate outcomes (if any)
            
        Returns:
            ConsensusResult with consensus determination
        """
        round_id = str(uuid.uuid4())
        
        logger.info(
            "consensus_computation_started",
            round_id=round_id,
            review_count=len(reviews),
            debate_count=len(debates)
        )
        
        # 1. Compute weighted vote
        vote_breakdown = self._compute_votes(reviews)
        weights_applied = self._get_weights_for_reviews(reviews)
        confidence = self._compute_confidence(vote_breakdown, weights_applied)
        
        # 2. Adjust confidence based on debates
        debate_adjustment = self._compute_debate_adjustment(debates)
        adjusted_confidence = min(1.0, confidence + debate_adjustment)
        
        # 3. Determine consensus
        agreed = adjusted_confidence >= self.threshold
        
        # 4. Identify resolved and unresolved disagreements
        disagreements_resolved = [
            d.debate_id for d in debates if d.consensus_reached
        ]
        disagreements_unresolved = [
            d.debate_id for d in debates if not d.consensus_reached
        ]
        
        # 5. Generate summary
        summary = self._generate_summary(
            agreed=agreed,
            confidence=adjusted_confidence,
            vote_breakdown=vote_breakdown,
            debates=debates
        )
        
        result = ConsensusResult(
            round_id=round_id,
            agreed=agreed,
            confidence=adjusted_confidence,
            summary=summary,
            disagreements_resolved=disagreements_resolved,
            disagreements_unresolved=disagreements_unresolved,
            vote_breakdown=vote_breakdown,
            weights_applied=weights_applied,
            threshold=self.threshold,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            "consensus_computation_completed",
            round_id=round_id,
            agreed=agreed,
            confidence=adjusted_confidence,
            resolved=len(disagreements_resolved),
            unresolved=len(disagreements_unresolved)
        )
        
        return result
    
    def _compute_votes(self, reviews: List[ReviewFeedback]) -> dict:
        """
        Compute vote breakdown from reviews.
        
        Returns:
            Dict mapping agent_role -> vote (approve/revise/reject)
        """
        votes = {}
        for review in reviews:
            votes[review.reviewer_role.value] = review.decision.value
        return votes
    
    def _get_weights_for_reviews(self, reviews: List[ReviewFeedback]) -> dict:
        """
        Get weights for each reviewer.
        
        Returns:
            Dict mapping agent_role -> weight
        """
        weights = {}
        for review in reviews:
            role = review.reviewer_role
            weights[role.value] = self.weights.get(role, self.weights.get("default", 0.05))
        return weights
    
    def _compute_confidence(
        self,
        vote_breakdown: dict,
        weights_applied: dict
    ) -> float:
        """
        Compute weighted confidence score.
        
        Logic:
        - APPROVE = +1.0 * weight
        - REVISE = +0.0 * weight (neutral)
        - REJECT = -0.5 * weight
        - ESCALATE = +0.3 * weight (slightly positive)
        
        Returns:
            Confidence score (0-1)
        """
        total_weight = sum(weights_applied.values())
        if total_weight == 0:
            return 0.0
        
        weighted_sum = 0.0
        for agent, vote in vote_breakdown.items():
            weight = weights_applied.get(agent, 0.0)
            
            if vote == ReviewDecision.APPROVE.value:
                weighted_sum += 1.0 * weight
            elif vote == ReviewDecision.REVISE.value:
                weighted_sum += 0.0 * weight
            elif vote == ReviewDecision.REJECT.value:
                weighted_sum += -0.5 * weight
            elif vote == ReviewDecision.ESCALATE.value:
                weighted_sum += 0.3 * weight
        
        # Normalize to 0-1 range
        # Max possible score is total_weight, min is -0.5 * total_weight
        # Shift and scale to 0-1
        confidence = (weighted_sum + 0.5 * total_weight) / (1.5 * total_weight)
        
        return max(0.0, min(1.0, confidence))
    
    def _compute_debate_adjustment(self, debates: List[DebateOutcome]) -> float:
        """
        Compute confidence adjustment based on debate outcomes.
        
        Debates that reach consensus boost confidence.
        Debates that don't reach consensus lower confidence.
        
        Returns:
            Adjustment value (-0.2 to +0.2)
        """
        if not debates:
            return 0.0
        
        resolved_count = sum(1 for d in debates if d.consensus_reached)
        unresolved_count = len(debates) - resolved_count
        
        # Each resolved debate adds +0.05, each unresolved subtracts -0.05
        adjustment = (resolved_count * 0.05) - (unresolved_count * 0.05)
        
        # Cap adjustment at ±0.2
        return max(-0.2, min(0.2, adjustment))
    
    def _generate_summary(
        self,
        agreed: bool,
        confidence: float,
        vote_breakdown: dict,
        debates: List[DebateOutcome]
    ) -> str:
        """Generate human-readable consensus summary."""
        approvals = sum(1 for v in vote_breakdown.values() if v == ReviewDecision.APPROVE.value)
        revisions = sum(1 for v in vote_breakdown.values() if v == ReviewDecision.REVISE.value)
        rejections = sum(1 for v in vote_breakdown.values() if v == ReviewDecision.REJECT.value)
        
        if agreed:
            if debates:
                resolved = sum(1 for d in debates if d.consensus_reached)
                summary = (
                    f"Consensus reached with {confidence:.1%} confidence. "
                    f"Votes: {approvals} approve, {revisions} revise, {rejections} reject. "
                    f"Resolved {resolved}/{len(debates)} debates."
                )
            else:
                summary = (
                    f"Consensus reached with {confidence:.1%} confidence. "
                    f"Votes: {approvals} approve, {revisions} revise, {rejections} reject."
                )
        else:
            if debates:
                unresolved = sum(1 for d in debates if not d.consensus_reached)
                summary = (
                    f"Consensus not reached ({confidence:.1%} confidence, threshold {self.threshold:.1%}). "
                    f"{unresolved} unresolved debate(s). Requires adjudication."
                )
            else:
                summary = (
                    f"Consensus not reached ({confidence:.1%} confidence, threshold {self.threshold:.1%}). "
                    f"Votes: {approvals} approve, {revisions} revise, {rejections} reject. "
                    "Requires adjudication."
                )
        
        return summary


def compute_consensus(
    reviews: List[ReviewFeedback],
    debates: Optional[List[DebateOutcome]] = None,
    threshold: float = DEFAULT_CONSENSUS_THRESHOLD
) -> ConsensusResult:
    """
    Compute consensus from reviews and debates.
    
    Convenience function for consensus computation.
    
    Args:
        reviews: Reviewer feedback
        debates: Debate outcomes (optional)
        threshold: Consensus threshold
        
    Returns:
        ConsensusResult
    """
    engine = ConsensusEngine(threshold=threshold)
    return engine.compute(reviews, debates or [])

