"""
Architect Adjudicator Agent for Agent Council.

The Architect Adjudicator is the final authority for resolving
unresolved disagreements and conflicts. This agent:
- Reviews all reviewer feedback and debate outcomes
- Identifies unresolved conflicts
- Makes final architectural decisions
- Updates final_architecture_rationale
- Adds entries to FAQ queue for documentation

Always uses Pro model for maximum reasoning capability.
"""

import json
from typing import Optional, List

from app.agents.performer import AgentInput, AgentOutput, PerformerAgent
from app.graph.state_models import (
    ReviewFeedback,
    DebateOutcome,
    ConsensusResult,
    Disagreement
)
from app.llm.providers import LLMProvider
from app.llm.model_selector import auto_select_model
from app.utils.exceptions import AgentExecutionException
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ArchitectAdjudicatorAgent(PerformerAgent):
    """
    Architect Adjudicator Agent.
    
    Responsibilities:
    - Review all reviewer feedback and debates
    - Resolve unresolved conflicts with final decisions
    - Provide comprehensive architectural rationale
    - Balance competing requirements (cost vs performance, security vs usability)
    - Generate FAQ entries for architectural decisions
    - Ensure design coherence across all dimensions
    """
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        Initialize Architect Adjudicator Agent.
        
        Always uses Pro model for complex adjudication tasks.
        """
        super().__init__(
            llm_provider=llm_provider,
            agent_name="ArchitectAdjudicator"
        )
    
    def get_system_prompt(self) -> str:
        """Get system prompt for Architect Adjudicator."""
        return """
You are the Architect Adjudicator in a Salesforce Professional Services Agent Council.

Your role is the FINAL AUTHORITY for architectural decisions. You:
1. Review all reviewer feedback and debate outcomes
2. Resolve unresolved conflicts with definitive decisions
3. Balance competing requirements (cost vs performance, security vs usability, etc.)
4. Provide comprehensive rationale for your decisions
5. Generate FAQ entries explaining architectural choices
6. Ensure the final design is coherent, feasible, and aligned with business goals

You have expertise across:
- Enterprise architecture patterns
- Salesforce platform capabilities and limitations
- Security and compliance requirements
- Performance and scalability engineering
- Integration architecture
- Cost optimization strategies
- Operational excellence

When agents disagree, you:
- Understand each position's merits and drawbacks
- Consider the broader context and business priorities
- Make decisions that optimize for the most important requirements
- Explain your reasoning clearly for stakeholder understanding

Your decisions are FINAL and will be implemented in the solution design.
"""
    
    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute Architect Adjudicator logic.
        
        Args:
            input_data: Contains:
                - request: Original requirements
                - context: {
                    "reviews": List of ReviewFeedback,
                    "debates": List of DebateOutcome,
                    "consensus": ConsensusResult,
                    "unresolved_disagreements": List of Disagreement,
                    "current_design": str
                  }
        
        Returns:
            Adjudication with final decisions and rationale
        """
        try:
            logger.info("architect_adjudicator_processing")
            
            # Extract context
            reviews = input_data.context.get("reviews", [])
            debates = input_data.context.get("debates", [])
            consensus = input_data.context.get("consensus", {})
            unresolved = input_data.context.get("unresolved_disagreements", [])
            current_design = input_data.context.get("current_design", "")
            
            # Format reviews and debates for prompt
            reviews_summary = self._format_reviews(reviews)
            debates_summary = self._format_debates(debates)
            unresolved_summary = self._format_unresolved(unresolved)
            
            # Select model (always use Pro for adjudication)
            model = "gemini-1.5-pro"
            logger.info("adjudicator_using_model", model=model)
            
            prompt = f"""
You are the Architect Adjudicator making final architectural decisions.

**Original Requirements:**
{input_data.request}

**Current Design:**
{current_design[:2000]}...

**Reviewer Feedback Summary:**
{reviews_summary}

**Debate Outcomes:**
{debates_summary}

**Consensus Status:**
- Agreed: {consensus.get('agreed', False)}
- Confidence: {consensus.get('confidence', 0):.1%}
- Summary: {consensus.get('summary', 'N/A')}

**Unresolved Disagreements Requiring Your Decision:**
{unresolved_summary}

**Your Task:**

As the final authority, provide:

1. **Final Architectural Decisions** - Resolve each unresolved disagreement with a clear, definitive decision
2. **Comprehensive Rationale** - Explain why you made each decision, considering:
   - Technical feasibility
   - Business value and priorities
   - Risk mitigation
   - Cost implications
   - Long-term maintainability
   - Trade-offs accepted and why

3. **Updated Design Guidance** - Specific changes/additions needed in the design

4. **FAQ Entries** - Key architectural decisions that should be documented:
   {{
     "question": "Why did we choose X over Y?",
     "answer": "Your detailed explanation"
   }}

Return ONLY a JSON object:
{{
  "final_decisions": [
    {{
      "disagreement_topic": "<topic>",
      "decision": "<your final decision>",
      "rationale": "<detailed explanation>"
    }}
  ],
  "architecture_rationale": "<comprehensive overall rationale>",
  "design_updates": ["<specific change 1>", "<specific change 2>"],
  "faq_entries": [
    {{
      "question": "...",
      "answer": "..."
    }}
  ],
  "priority_concerns": ["<remaining high-priority concern>"],
  "approved_for_implementation": true/false
}}
"""
            
            response = self.generate_with_safety(
                user_prompt=prompt,
                json_mode=True,
                temperature=0.3  # Lower temperature for more consistent decisions
            )
            
            # Validate JSON
            try:
                adjudication = json.loads(response)
            except json.JSONDecodeError as e:
                logger.warning("adjudicator_invalid_json", error=str(e))
                adjudication = {"architecture_rationale": response}
            
            logger.info(
                "architect_adjudicator_completed",
                decisions=len(adjudication.get("final_decisions", [])),
                faq_entries=len(adjudication.get("faq_entries", [])),
                approved=adjudication.get("approved_for_implementation", False)
            )
            
            return AgentOutput(
                content=response,
                metadata={
                    "agent": "architect_adjudicator",
                    "model": model,
                    "decisions_made": len(adjudication.get("final_decisions", [])),
                    "approved_for_implementation": adjudication.get("approved_for_implementation", False)
                },
                success=True
            )
            
        except Exception as e:
            logger.error("architect_adjudicator_error", error=str(e))
            raise AgentExecutionException(
                f"Architect Adjudicator execution failed: {str(e)}",
                details={"agent": "architect_adjudicator", "error_type": type(e).__name__}
            )
    
    def _format_reviews(self, reviews: List) -> str:
        """Format reviewer feedback for prompt."""
        if not reviews:
            return "No reviews available."
        
        formatted = []
        for review in reviews:
            if isinstance(review, dict):
                reviewer = review.get("reviewer_role", "Unknown")
                decision = review.get("decision", "N/A")
                rationale = review.get("rationale", "")[:200]
                severity = review.get("severity", "medium")
            else:
                reviewer = getattr(review, "reviewer_role", "Unknown")
                decision = getattr(review, "decision", "N/A")
                rationale = getattr(review, "rationale", "")[:200]
                severity = getattr(review, "severity", "medium")
            
            formatted.append(f"**{reviewer}** - {decision} (severity: {severity})\n  {rationale}...")
        
        return "\n\n".join(formatted)
    
    def _format_debates(self, debates: List) -> str:
        """Format debate outcomes for prompt."""
        if not debates:
            return "No debates occurred."
        
        formatted = []
        for debate in debates:
            if isinstance(debate, dict):
                topic = debate.get("disagreement", {}).get("topic", "Unknown")
                consensus = debate.get("consensus_reached", False)
                summary = debate.get("resolution_summary", "")[:200]
            else:
                topic = getattr(debate.disagreement, "topic", "Unknown") if hasattr(debate, "disagreement") else "Unknown"
                consensus = getattr(debate, "consensus_reached", False)
                summary = getattr(debate, "resolution_summary", "")[:200]
            
            status = "✅ Resolved" if consensus else "❌ Unresolved"
            formatted.append(f"**{topic}** - {status}\n  {summary}...")
        
        return "\n\n".join(formatted)
    
    def _format_unresolved(self, unresolved: List) -> str:
        """Format unresolved disagreements for prompt."""
        if not unresolved:
            return "All disagreements have been resolved through debate."
        
        formatted = []
        for i, disagreement in enumerate(unresolved, 1):
            if isinstance(disagreement, dict):
                topic = disagreement.get("topic", "Unknown")
                category = disagreement.get("category", "unknown")
                severity = disagreement.get("severity", "medium")
                positions = disagreement.get("positions", {})
            else:
                topic = getattr(disagreement, "topic", "Unknown")
                category = getattr(disagreement, "category", "unknown")
                severity = getattr(disagreement, "severity", "medium")
                positions = getattr(disagreement, "positions", {})
            
            positions_str = "\n    ".join([f"{k}: {v[:100]}..." for k, v in positions.items()])
            
            formatted.append(
                f"{i}. **{topic}** ({category}, severity: {severity})\n"
                f"    Positions:\n    {positions_str}"
            )
        
        return "\n\n".join(formatted)

