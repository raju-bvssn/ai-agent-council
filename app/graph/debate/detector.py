"""
Disagreement detection module for Agent Council.

Analyzes reviewer feedback to identify conflicting recommendations,
opposing patterns, and areas requiring debate or adjudication.
"""

import uuid
from typing import List
from datetime import datetime

from app.graph.state_models import ReviewFeedback, Disagreement, ReviewDecision, AgentRole
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Opposing pattern keywords
OPPOSING_PATTERNS = {
    "sync_vs_async": {
        "sync": ["synchronous", "sync", "real-time", "immediate", "blocking"],
        "async": ["asynchronous", "async", "eventual consistency", "non-blocking", "queue"]
    },
    "monolith_vs_microservices": {
        "monolith": ["monolithic", "single application", "tightly coupled"],
        "microservices": ["microservices", "distributed", "loosely coupled", "service mesh"]
    },
    "sql_vs_nosql": {
        "sql": ["relational", "sql", "acid", "normalized"],
        "nosql": ["nosql", "document store", "key-value", "eventually consistent"]
    },
    "rest_vs_graphql": {
        "rest": ["rest", "restful", "resource-based"],
        "graphql": ["graphql", "query language", "single endpoint"]
    },
    "cost_vs_performance": {
        "cost_optimized": ["cost-effective", "economical", "budget", "cheaper"],
        "performance_optimized": ["high performance", "low latency", "fast", "optimized for speed"]
    }
}


def detect_disagreements(reviews: List[ReviewFeedback]) -> List[Disagreement]:
    """
    Detect disagreements between reviewer agents.
    
    Identifies:
    - Contradictory decisions (approve vs revise/reject)
    - Opposing pattern recommendations
    - Conflicting technical approaches
    - Cost vs performance tradeoffs
    
    Args:
        reviews: List of reviewer feedback from a round
        
    Returns:
        List of detected disagreements
    """
    disagreements = []
    
    if len(reviews) < 2:
        logger.info("disagreement_detection_skipped", reason="insufficient_reviews", count=len(reviews))
        return disagreements
    
    logger.info("disagreement_detection_started", review_count=len(reviews))
    
    # 1. Detect decision conflicts
    decision_conflicts = _detect_decision_conflicts(reviews)
    disagreements.extend(decision_conflicts)
    
    # 2. Detect pattern conflicts
    pattern_conflicts = _detect_pattern_conflicts(reviews)
    disagreements.extend(pattern_conflicts)
    
    # 3. Detect concern overlaps (same issue, different severity assessments)
    concern_conflicts = _detect_concern_severity_conflicts(reviews)
    disagreements.extend(concern_conflicts)
    
    logger.info(
        "disagreement_detection_completed",
        total_disagreements=len(disagreements),
        by_type={
            "decision": len(decision_conflicts),
            "pattern": len(pattern_conflicts),
            "concern": len(concern_conflicts)
        }
    )
    
    return disagreements


def _detect_decision_conflicts(reviews: List[ReviewFeedback]) -> List[Disagreement]:
    """Detect conflicting approve/revise/reject decisions."""
    conflicts = []
    
    # Group by decision
    approvals = [r for r in reviews if r.decision == ReviewDecision.APPROVE]
    revisions = [r for r in reviews if r.decision == ReviewDecision.REVISE]
    rejections = [r for r in reviews if r.decision == ReviewDecision.REJECT]
    
    # If we have both approvals and revisions/rejections, that's a conflict
    if approvals and (revisions or rejections):
        conflict = Disagreement(
            disagreement_id=str(uuid.uuid4()),
            agent_roles=[r.reviewer_role for r in reviews],
            topic="Overall Design Approval",
            positions={
                r.reviewer_role.value: f"{r.decision.value}: {r.rationale[:100]}..."
                for r in reviews
            },
            severity=analyze_conflict_severity(reviews),
            category="decision_conflict",
            detected_at=datetime.utcnow()
        )
        conflicts.append(conflict)
        logger.info("decision_conflict_detected", agents=[r.reviewer_role.value for r in reviews])
    
    return conflicts


def _detect_pattern_conflicts(reviews: List[ReviewFeedback]) -> List[Disagreement]:
    """Detect opposing pattern recommendations."""
    conflicts = []
    
    # Combine all suggestions and concerns from all reviews
    all_text = " ".join([
        " ".join(r.suggestions + r.concerns)
        for r in reviews
    ]).lower()
    
    # Check each opposing pattern
    for pattern_name, pattern_dict in OPPOSING_PATTERNS.items():
        sides_detected = {}
        
        for side_name, keywords in pattern_dict.items():
            for keyword in keywords:
                if keyword in all_text:
                    # Find which agent(s) mentioned this side
                    for review in reviews:
                        review_text = " ".join(review.suggestions + review.concerns).lower()
                        if keyword in review_text:
                            if side_name not in sides_detected:
                                sides_detected[side_name] = []
                            if review.reviewer_role not in sides_detected[side_name]:
                                sides_detected[side_name].append(review.reviewer_role)
        
        # If we have both sides mentioned by different agents, it's a conflict
        if len(sides_detected) >= 2:
            # Get agents for each side
            side_agents = {}
            for side, agents in sides_detected.items():
                for agent in agents:
                    if agent not in side_agents:
                        side_agents[agent] = []
                    side_agents[agent].append(side)
            
            # Create disagreement
            conflict = Disagreement(
                disagreement_id=str(uuid.uuid4()),
                agent_roles=list(sides_detected.values())[0] + list(sides_detected.values())[1],
                topic=f"Technical Approach: {pattern_name.replace('_', ' ').title()}",
                positions={
                    agent.value: f"Recommends {sides[0]}"
                    for agent, sides in side_agents.items()
                },
                severity="medium",
                category=f"pattern_conflict_{pattern_name}",
                detected_at=datetime.utcnow()
            )
            conflicts.append(conflict)
            logger.info("pattern_conflict_detected", pattern=pattern_name, sides=list(sides_detected.keys()))
    
    return conflicts


def _detect_concern_severity_conflicts(reviews: List[ReviewFeedback]) -> List[Disagreement]:
    """Detect when agents have overlapping concerns but different severity assessments."""
    conflicts = []
    
    # Group reviews by concerns
    concern_map = {}
    for review in reviews:
        for concern in review.concerns:
            concern_lower = concern.lower()
            # Simple keyword matching for overlapping concerns
            if concern_lower not in concern_map:
                concern_map[concern_lower] = []
            concern_map[concern_lower].append((review.reviewer_role, review.severity))
    
    # Find concerns mentioned by multiple agents with different severities
    for concern, agent_severities in concern_map.items():
        if len(agent_severities) >= 2:
            severities = set([sev for _, sev in agent_severities])
            if len(severities) > 1:
                conflict = Disagreement(
                    disagreement_id=str(uuid.uuid4()),
                    agent_roles=[agent for agent, _ in agent_severities],
                    topic=f"Severity Assessment: {concern[:50]}...",
                    positions={
                        agent.value: f"Severity: {sev}"
                        for agent, sev in agent_severities
                    },
                    severity="low",
                    category="severity_conflict",
                    detected_at=datetime.utcnow()
                )
                conflicts.append(conflict)
                logger.info("severity_conflict_detected", concern=concern[:50], severities=list(severities))
    
    return conflicts


def analyze_conflict_severity(reviews: List[ReviewFeedback]) -> str:
    """
    Analyze the severity of a conflict based on reviewer assessments.
    
    Args:
        reviews: Reviewer feedback involved in conflict
        
    Returns:
        Severity level: low, medium, high, critical
    """
    # Count severity levels
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    for review in reviews:
        severity = review.severity.lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    # Determine overall severity
    if severity_counts["critical"] > 0:
        return "critical"
    elif severity_counts["high"] > 1:
        return "high"
    elif severity_counts["high"] > 0 or severity_counts["medium"] > 1:
        return "medium"
    else:
        return "low"


def categorize_disagreements(disagreements: List[Disagreement]) -> dict:
    """
    Categorize disagreements for reporting.
    
    Args:
        disagreements: List of disagreements
        
    Returns:
        Dict with categorized disagreements
    """
    categorized = {
        "decision_conflicts": [],
        "pattern_conflicts": [],
        "severity_conflicts": [],
        "other": []
    }
    
    for disagreement in disagreements:
        if "decision" in disagreement.category:
            categorized["decision_conflicts"].append(disagreement)
        elif "pattern" in disagreement.category:
            categorized["pattern_conflicts"].append(disagreement)
        elif "severity" in disagreement.category:
            categorized["severity_conflicts"].append(disagreement)
        else:
            categorized["other"].append(disagreement)
    
    return categorized

