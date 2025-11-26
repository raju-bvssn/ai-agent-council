"""
Debate and consensus modules for Agent Council.

Handles disagreement detection, multi-agent debates, and consensus building.
"""

from app.graph.debate.detector import detect_disagreements, analyze_conflict_severity
from app.graph.debate.debate_engine import run_debate, DebateEngine
from app.graph.debate.consensus import compute_consensus, ConsensusEngine

__all__ = [
    "detect_disagreements",
    "analyze_conflict_severity",
    "run_debate",
    "DebateEngine",
    "compute_consensus",
    "ConsensusEngine",
]

