"""
Debate engine for Agent Council.

Facilitates structured debates between disagreeing agents to reach
consensus or prepare for adjudication.
"""

import asyncio
import uuid
from typing import List, Optional
from datetime import datetime

from app.graph.state_models import Disagreement, DebateOutcome, AgentRole
from app.llm.factory import get_llm_provider
from app.llm.model_selector import auto_select_model
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DebateEngine:
    """
    Engine for facilitating micro-debates between agents.
    
    Manages debate rounds, position revisions, and consensus assessment.
    """
    
    def __init__(self, max_rounds: int = 2, model: Optional[str] = None):
        """
        Initialize debate engine.
        
        Args:
            max_rounds: Maximum number of debate rounds
            model: Model to use for debate facilitation (auto-selected if None)
        """
        self.max_rounds = max_rounds
        self.model = model
        self.provider = get_llm_provider()
        logger.info("debate_engine_initialized", max_rounds=max_rounds, model=model)
    
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
        
        # Conduct debate rounds
        for round_num in range(1, self.max_rounds + 1):
            logger.info("debate_round_started", debate_id=debate_id, round=round_num)
            
            round_result = await self._conduct_debate_round(
                disagreement=disagreement,
                current_positions=revised_positions,
                round_number=round_num,
                context=context,
                model=model
            )
            
            debate_history.append(round_result)
            revised_positions = round_result["revised_positions"]
            
            # Check if consensus reached
            if round_result["consensus_reached"]:
                logger.info("debate_consensus_reached", debate_id=debate_id, round=round_num)
                break
        
        # Final assessment
        consensus_reached, confidence, resolution_summary = self._assess_final_consensus(
            disagreement=disagreement,
            initial_positions=disagreement.positions,
            final_positions=revised_positions,
            debate_history=debate_history,
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
        context: str,
        model: str
    ) -> tuple[bool, float, str]:
        """
        Assess whether consensus was reached and compute confidence.
        
        Returns:
            (consensus_reached, confidence_score, summary)
        """
        # Simple heuristic: if positions converged significantly, consensus reached
        convergence = self._measure_convergence(initial_positions, final_positions)
        
        # Consensus reached if:
        # 1. Explicit consensus in last round, OR
        # 2. High convergence (>0.7)
        consensus_reached = False
        if debate_history:
            last_round = debate_history[-1]
            consensus_reached = last_round.get("consensus_reached", False)
        
        if not consensus_reached and convergence > 0.7:
            consensus_reached = True
        
        confidence = convergence
        
        # Generate summary
        if consensus_reached:
            summary = f"Consensus reached after {len(debate_history)} round(s). Agents converged on a unified approach."
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
    max_rounds: int = 2
) -> DebateOutcome:
    """
    Run a debate for a single disagreement.
    
    Convenience function for debate execution.
    
    Args:
        disagreement: Disagreement to resolve
        context: Design context
        model: Optional model override
        max_rounds: Maximum debate rounds
        
    Returns:
        DebateOutcome with resolution
    """
    engine = DebateEngine(max_rounds=max_rounds, model=model)
    return await engine.facilitate_debate(disagreement, context)


async def run_debates_parallel(
    disagreements: List[Disagreement],
    context: str,
    model: Optional[str] = None,
    max_rounds: int = 2
) -> List[DebateOutcome]:
    """
    Run multiple debates in parallel.
    
    Args:
        disagreements: List of disagreements to resolve
        context: Design context
        model: Optional model override
        max_rounds: Maximum debate rounds
        
    Returns:
        List of DebateOutcome results
    """
    if not disagreements:
        return []
    
    logger.info("debates_parallel_started", count=len(disagreements))
    
    # Create debate tasks
    tasks = [
        run_debate(disagreement, context, model, max_rounds)
        for disagreement in disagreements
    ]
    
    # Execute in parallel
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_outcomes = []
    for i, outcome in enumerate(outcomes):
        if isinstance(outcome, Exception):
            logger.error("debate_failed", disagreement_id=disagreements[i].disagreement_id, error=str(outcome))
        else:
            valid_outcomes.append(outcome)
    
    logger.info("debates_parallel_completed", completed=len(valid_outcomes), failed=len(disagreements) - len(valid_outcomes))
    
    return valid_outcomes

