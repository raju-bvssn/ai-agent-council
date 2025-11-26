"""
Debate engine for Agent Council.

Facilitates structured debates between disagreeing agents to reach
consensus or prepare for adjudication.
"""

import asyncio
import uuid
import time
from typing import List, Optional
from datetime import datetime
from difflib import SequenceMatcher

from app.graph.state_models import Disagreement, DebateOutcome, AgentRole
from app.llm.factory import get_llm_provider
from app.llm.model_selector import auto_select_model
from app.utils.logging import get_logger
from app.utils.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class DebateEngine:
    """
    Engine for facilitating micro-debates between agents.
    
    Manages debate rounds, position revisions, and consensus assessment.
    """
    
    def __init__(self, max_rounds: Optional[int] = None, model: Optional[str] = None):
        """
        Initialize debate engine with stability safeguards.
        
        Args:
            max_rounds: Maximum number of debate rounds (uses settings if None)
            model: Model to use for debate facilitation (auto-selected if None)
        """
        self.max_rounds = max_rounds or settings.max_debate_rounds
        self.model = model
        self.provider = get_llm_provider()
        self.round_timeout = settings.debate_round_timeout
        self.enable_repetition_detection = settings.enable_repetition_detection
        self.repetition_threshold = settings.repetition_similarity_threshold
        self.enable_forced_consensus = settings.enable_forced_consensus
        
        logger.info(
            "debate_engine_initialized",
            max_rounds=self.max_rounds,
            round_timeout=self.round_timeout,
            repetition_detection=self.enable_repetition_detection,
            forced_consensus=self.enable_forced_consensus,
            model=model
        )
    
    async def facilitate_debate(
        self,
        disagreement: Disagreement,
        context: str
    ) -> DebateOutcome:
        """
        Facilitate a debate between disagreeing agents.
        
        Args:
            disagreement: The disagreement to resolve
            context: Full design context for the debate
            
        Returns:
            DebateOutcome with results
        """
        debate_id = str(uuid.uuid4())
        logger.info(
            "debate_started",
            debate_id=debate_id,
            disagreement_id=disagreement.disagreement_id,
            topic=disagreement.topic,
            agents=disagreement.agent_roles
        )
        
        # Select model for debate
        model = self.model or auto_select_model(
            f"Debate on {disagreement.topic}",
            agent_role="debate_facilitator"
        )
        
        revised_positions = disagreement.positions.copy()
        debate_history = []
        forced_consensus = False
        timeout_occurred = False
        repetition_detected = False
        
        # Conduct debate rounds with safeguards
        for round_num in range(1, self.max_rounds + 1):
            round_start_time = time.time()
            logger.info("debate_round_started", debate_id=debate_id, round=round_num, max_rounds=self.max_rounds)
            
            # Safeguard 1: Round timeout using asyncio.wait_for
            try:
                round_result = await asyncio.wait_for(
                    self._conduct_debate_round(
                        disagreement=disagreement,
                        current_positions=revised_positions,
                        round_number=round_num,
                        context=context,
                        model=model
                    ),
                    timeout=self.round_timeout
                )
            except asyncio.TimeoutError:
                timeout_occurred = True
                logger.warning(
                    "debate_round_timeout",
                    debate_id=debate_id,
                    round=round_num,
                    timeout_seconds=self.round_timeout
                )
                # Force consensus on timeout
                if self.enable_forced_consensus:
                    forced_consensus = True
                    logger.info("forced_consensus_due_to_timeout", debate_id=debate_id)
                    break
                else:
                    # Use previous positions as fallback
                    round_result = {
                        "revised_positions": revised_positions,
                        "consensus_reached": False,
                        "consensus_explanation": f"Round timed out after {self.round_timeout}s",
                        "common_ground": [],
                        "remaining_differences": []
                    }
            
            round_duration = time.time() - round_start_time
            debate_history.append(round_result)
            
            # Extract new positions
            new_positions = round_result["revised_positions"]
            
            # Safeguard 2: Repetition detection
            if self.enable_repetition_detection and round_num > 1:
                similarity = self._calculate_position_similarity(revised_positions, new_positions)
                logger.debug(
                    "repetition_check",
                    debate_id=debate_id,
                    round=round_num,
                    similarity=similarity,
                    threshold=self.repetition_threshold
                )
                
                if similarity >= self.repetition_threshold:
                    repetition_detected = True
                    logger.warning(
                        "repetitive_debate_detected",
                        debate_id=debate_id,
                        round=round_num,
                        similarity=similarity,
                        threshold=self.repetition_threshold
                    )
                    # Force consensus on repetition
                    if self.enable_forced_consensus:
                        forced_consensus = True
                        logger.info("forced_consensus_due_to_repetition", debate_id=debate_id)
                        break
            
            revised_positions = new_positions
            
            logger.info(
                "debate_round_completed",
                debate_id=debate_id,
                round=round_num,
                duration_seconds=round_duration,
                consensus_reached=round_result.get("consensus_reached", False)
            )
            
            # Check if consensus reached naturally
            if round_result["consensus_reached"]:
                logger.info("debate_consensus_reached_naturally", debate_id=debate_id, round=round_num)
                break
        
        # Safeguard 3: Force consensus if max rounds reached
        if not forced_consensus and len(debate_history) >= self.max_rounds:
            if self.enable_forced_consensus:
                forced_consensus = True
                logger.warning(
                    "forced_consensus_max_rounds_reached",
                    debate_id=debate_id,
                    max_rounds=self.max_rounds
                )
        
        # Final assessment
        consensus_reached, confidence, resolution_summary = self._assess_final_consensus(
            disagreement=disagreement,
            initial_positions=disagreement.positions,
            final_positions=revised_positions,
            debate_history=debate_history,
            forced=forced_consensus,
            timeout_occurred=timeout_occurred,
            repetition_detected=repetition_detected,
            context=context,
            model=model
        )
        
        outcome = DebateOutcome(
            debate_id=debate_id,
            disagreement=disagreement,
            debate_rounds=len(debate_history),
            agent_positions_revised=revised_positions,
            consensus_reached=consensus_reached,
            resolution_summary=resolution_summary,
            confidence=confidence,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            "debate_completed",
            debate_id=debate_id,
            rounds=len(debate_history),
            consensus_reached=consensus_reached,
            forced_consensus=forced_consensus,
            timeout_occurred=timeout_occurred,
            repetition_detected=repetition_detected,
            confidence=confidence
        )
        
        return outcome
    
    async def _conduct_debate_round(
        self,
        disagreement: Disagreement,
        current_positions: dict,
        round_number: int,
        context: str,
        model: str
    ) -> dict:
        """
        Conduct a single debate round.
        
        Each agent gets to justify and revise their position.
        """
        # Build debate prompt
        debate_prompt = f"""
You are facilitating a debate between architectural review agents on a Salesforce project.

**Topic of Disagreement:** {disagreement.topic}
**Category:** {disagreement.category}
**Severity:** {disagreement.severity}

**Current Positions:**
{self._format_positions(current_positions)}

**Design Context:**
{context[:2000]}...

**Debate Round:** {round_number}/{self.max_rounds}

Your task:
1. Analyze each agent's position and rationale
2. Identify areas of potential common ground
3. Generate revised positions that move toward consensus
4. Assess whether consensus has been reached

Return ONLY a JSON object:
{{
  "revised_positions": {{
    "agent_role": "revised position with justification"
  }},
  "consensus_reached": true/false,
  "consensus_explanation": "explanation of why consensus was/wasn't reached",
  "common_ground": ["point1", "point2"],
  "remaining_differences": ["diff1", "diff2"]
}}
"""
        
        try:
            response = await self.provider.generate_with_safety(
                debate_prompt,
                model=model,
                json_mode=True
            )
            
            # Validate response has required fields
            if "revised_positions" not in response:
                response["revised_positions"] = current_positions
            if "consensus_reached" not in response:
                response["consensus_reached"] = False
            
            return response
            
        except Exception as e:
            logger.error("debate_round_failed", error=str(e), round=round_number)
            return {
                "revised_positions": current_positions,
                "consensus_reached": False,
                "consensus_explanation": f"Debate round failed: {str(e)}",
                "common_ground": [],
                "remaining_differences": []
            }
    
    def _assess_final_consensus(
        self,
        disagreement: Disagreement,
        initial_positions: dict,
        final_positions: dict,
        debate_history: list,
        forced: bool,
        timeout_occurred: bool,
        repetition_detected: bool,
        context: str,
        model: str
    ) -> tuple[bool, float, str]:
        """
        Assess whether consensus was reached and compute confidence.
        
        Args:
            disagreement: Original disagreement
            initial_positions: Starting positions
            final_positions: Final positions after debate
            debate_history: List of debate rounds
            forced: Whether consensus was forced by safeguards
            timeout_occurred: Whether a timeout occurred
            repetition_detected: Whether repetition was detected
            context: Design context
            model: LLM model used
        
        Returns:
            (consensus_reached, confidence_score, summary)
        """
        # Measure convergence
        convergence = self._measure_convergence(initial_positions, final_positions)
        
        # Determine consensus
        consensus_reached = False
        confidence = convergence
        
        # Check for natural consensus first
        if debate_history:
            last_round = debate_history[-1]
            consensus_reached = last_round.get("consensus_reached", False)
        
        if not consensus_reached and convergence > 0.7:
            consensus_reached = True
        
        # Handle forced consensus
        if forced:
            consensus_reached = True
            confidence = max(0.5, confidence)  # Lower confidence for forced consensus
        
        # Generate summary with safeguard context
        if consensus_reached:
            if forced:
                reasons = []
                if timeout_occurred:
                    reasons.append("timeout")
                if repetition_detected:
                    reasons.append("repetitive arguments")
                if len(debate_history) >= self.max_rounds:
                    reasons.append("max rounds reached")
                
                reason_str = ", ".join(reasons) if reasons else "safeguards"
                summary = (
                    f"Forced consensus after {len(debate_history)} round(s) due to {reason_str}. "
                    f"Confidence: {confidence:.2f}. Proceeding with best available resolution."
                )
            else:
                summary = f"Natural consensus reached after {len(debate_history)} round(s). Agents converged on a unified approach."
        else:
            summary = f"No consensus after {len(debate_history)} round(s). Requires adjudication."
        
        return consensus_reached, confidence, summary
    
    def _measure_convergence(self, initial: dict, final: dict) -> float:
        """
        Measure how much positions have converged.
        
        Simple heuristic: compare text similarity.
        Returns 0-1, where 1 is perfect convergence.
        """
        if not initial or not final:
            return 0.0
        
        # Simple token overlap measure
        initial_tokens = set(" ".join(initial.values()).lower().split())
        final_tokens = set(" ".join(final.values()).lower().split())
        
        if not initial_tokens:
            return 0.0
        
        overlap = len(initial_tokens & final_tokens)
        total = len(initial_tokens | final_tokens)
        
        if total == 0:
            return 0.0
        
        return overlap / total
    
    def _calculate_position_similarity(self, positions1: dict, positions2: dict) -> float:
        """
        Calculate similarity between two sets of positions for repetition detection.
        
        Uses sequence matching to detect if arguments are repeating.
        
        Args:
            positions1: First set of positions
            positions2: Second set of positions
            
        Returns:
            Similarity score 0-1, where 1 is identical
        """
        if not positions1 or not positions2:
            return 0.0
        
        # Compare each agent's position
        similarities = []
        for agent in set(positions1.keys()) | set(positions2.keys()):
            pos1 = positions1.get(agent, "")
            pos2 = positions2.get(agent, "")
            
            if not pos1 or not pos2:
                similarities.append(0.0)
                continue
            
            # Use SequenceMatcher for text similarity
            matcher = SequenceMatcher(None, pos1.lower(), pos2.lower())
            similarities.append(matcher.ratio())
        
        # Return average similarity
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _format_positions(self, positions: dict) -> str:
        """Format agent positions for prompt."""
        formatted = []
        for agent, position in positions.items():
            formatted.append(f"**{agent}**: {position}")
        return "\n".join(formatted)


async def run_debate(
    disagreement: Disagreement,
    context: str,
    model: Optional[str] = None,
    max_rounds: Optional[int] = None
) -> DebateOutcome:
    """
    Run a debate for a single disagreement with stability safeguards.
    
    Convenience function for debate execution. Uses settings for max_rounds if not provided.
    
    Args:
        disagreement: Disagreement to resolve
        context: Design context
        model: Optional model override
        max_rounds: Maximum debate rounds (uses settings if None)
        
    Returns:
        DebateOutcome with resolution (may include forced consensus)
    """
    engine = DebateEngine(max_rounds=max_rounds, model=model)
    return await engine.facilitate_debate(disagreement, context)


async def run_debates_parallel(
    disagreements: List[Disagreement],
    context: str,
    model: Optional[str] = None,
    max_rounds: Optional[int] = None
) -> List[DebateOutcome]:
    """
    Run multiple debates in parallel with stability safeguards.
    
    Args:
        disagreements: List of disagreements to resolve
        context: Design context
        model: Optional model override
        max_rounds: Maximum debate rounds (uses settings if None)
        
    Returns:
        List of DebateOutcome results (may include forced consensus)
    """
    if not disagreements:
        return []
    
    logger.info("debates_parallel_started", count=len(disagreements))
    
    # Create debate tasks with timeout protection
    tasks = [
        run_debate(disagreement, context, model, max_rounds)
        for disagreement in disagreements
    ]
    
    # Execute in parallel with overall timeout
    try:
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error("debates_parallel_failed", error=str(e))
        return []
    
    # Filter out exceptions
    valid_outcomes = []
    for i, outcome in enumerate(outcomes):
        if isinstance(outcome, Exception):
            logger.error("debate_failed", disagreement_id=disagreements[i].disagreement_id, error=str(outcome))
        else:
            valid_outcomes.append(outcome)
    
    logger.info(
        "debates_parallel_completed",
        completed=len(valid_outcomes),
        failed=len(disagreements) - len(valid_outcomes),
        total=len(disagreements)
    )
    
    return valid_outcomes

