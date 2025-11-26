"""
Debate and consensus modules for Agent Council.

Handles disagreement detection, multi-agent debates, and consensus building.
"""

from app.graph.debate.detector import detect_disagreements, analyze_conflict_severity
from app.graph.debate.debate_engine import run_debate, run_debates_parallel, DebateEngine
from app.graph.debate.consensus import compute_consensus, ConsensusEngine

__all__ = [
    "detect_disagreements",
    "analyze_conflict_severity",
    "run_debate",
    "run_debates_parallel",
    "DebateEngine",
    "compute_consensus",
    "ConsensusEngine",
]

