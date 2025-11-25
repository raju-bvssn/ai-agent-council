"""
Agent role suggestion engine for Agent Council.

Analyzes user requirements and suggests relevant specialist agents
with recommended tools and responsibilities.
"""

from typing import List
from pydantic import BaseModel


class SuggestedRole(BaseModel):
    """
    Suggested agent role with configuration.
    """
    name: str
    description: str
    default_responsibilities: str
    recommended_tools: List[str]
    category: str  # integration, security, performance, etc.


def suggest_roles(description: str) -> List[SuggestedRole]:
    """
    Suggest agent roles based on user description.
    
    Args:
        description: User's requirement description
        
    Returns:
        List of suggested roles with configurations
    """
    # For Phase 1, return a curated list of common Salesforce/MuleSoft roles
    # TODO: Phase 2 - Use LLM to analyze description and suggest contextual roles
    
    base_roles = [
        SuggestedRole(
            name="Master Architect",
            description="Orchestrates the council, synthesizes recommendations, and ensures alignment with business goals.",
            default_responsibilities="Lead overall design strategy. Coordinate between specialists. Ensure solution coherence. Validate against business requirements.",
            recommended_tools=["Gemini", "NotebookLM"],
            category="leadership"
        ),
        SuggestedRole(
            name="Solution Architect",
            description="Designs comprehensive solution architecture with components, integrations, and deployment strategy.",
            default_responsibilities="Create detailed design documents. Define component architecture. Specify integration patterns. Document deployment approach.",
            recommended_tools=["Gemini", "Lucid AI", "NotebookLM"],
            category="architecture"
        ),
        SuggestedRole(
            name="MuleSoft Integration Specialist",
            description="Expert in MuleSoft integration patterns, API-led connectivity, and Anypoint Platform best practices.",
            default_responsibilities="Design Mule flows. Define API specifications. Recommend integration patterns. Ensure Anypoint Platform compliance.",
            recommended_tools=["Gemini", "Vibes", "MCP Server"],
            category="integration"
        ),
        SuggestedRole(
            name="API Security Reviewer",
            description="Reviews API security architecture, authentication, authorization, and data protection strategies.",
            default_responsibilities="Validate OAuth/SAML implementations. Review API gateway policies. Assess encryption strategies. Ensure compliance standards.",
            recommended_tools=["Gemini", "MCP Server"],
            category="security"
        ),
        SuggestedRole(
            name="Performance & Scalability Analyst",
            description="Analyzes throughput, latency, caching strategies, and scalability considerations for high-volume scenarios.",
            default_responsibilities="Define performance requirements. Identify bottlenecks. Recommend caching strategies. Validate scalability approach.",
            recommended_tools=["Gemini", "MCP Server"],
            category="performance"
        ),
        SuggestedRole(
            name="Data Integration Architect",
            description="Specializes in data mapping, transformation, batch processing, and ETL/ELT patterns.",
            default_responsibilities="Design data transformation logic. Define ETL workflows. Recommend data validation strategies. Ensure data quality.",
            recommended_tools=["Gemini", "Vibes"],
            category="data"
        ),
        SuggestedRole(
            name="Cost Optimization Advisor",
            description="Analyzes resource utilization, recommends efficient architecture patterns, and identifies cost-saving opportunities.",
            default_responsibilities="Estimate resource costs. Identify optimization opportunities. Recommend efficient patterns. Validate licensing approach.",
            recommended_tools=["Gemini", "MCP Server"],
            category="optimization"
        ),
        SuggestedRole(
            name="FAQ & Documentation Agent",
            description="Generates comprehensive documentation, FAQs, and decision rationale from council discussions.",
            default_responsibilities="Extract key decisions. Generate FAQ entries. Document design rationale. Create stakeholder summaries.",
            recommended_tools=["Gemini", "NotebookLM"],
            category="documentation"
        ),
    ]
    
    # Filter based on keywords in description (simple keyword matching for Phase 1)
    description_lower = description.lower() if description else ""
    
    # Always include Master Architect and Solution Architect
    suggested = [base_roles[0], base_roles[1]]
    
    # Add contextual roles based on keywords
    if any(keyword in description_lower for keyword in ["api", "integration", "mulesoft", "connect", "endpoint"]):
        suggested.append(base_roles[2])  # MuleSoft Integration Specialist
    
    if any(keyword in description_lower for keyword in ["security", "auth", "oauth", "encrypt", "secure"]):
        suggested.append(base_roles[3])  # API Security Reviewer
    
    if any(keyword in description_lower for keyword in ["performance", "scale", "throughput", "latency", "volume", "speed"]):
        suggested.append(base_roles[4])  # Performance Analyst
    
    if any(keyword in description_lower for keyword in ["data", "transform", "etl", "batch", "mapping"]):
        suggested.append(base_roles[5])  # Data Integration Architect
    
    if any(keyword in description_lower for keyword in ["cost", "budget", "optimize", "efficient", "resource"]):
        suggested.append(base_roles[6])  # Cost Optimization Advisor
    
    # Always add FAQ agent
    suggested.append(base_roles[7])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_suggested = []
    for role in suggested:
        if role.name not in seen:
            seen.add(role.name)
            unique_suggested.append(role)
    
    # Ensure we return 5-8 roles
    if len(unique_suggested) < 5:
        # Add remaining roles to reach minimum of 5
        for role in base_roles:
            if role.name not in seen:
                unique_suggested.append(role)
                seen.add(role.name)
                if len(unique_suggested) >= 5:
                    break
    
    return unique_suggested[:8]  # Max 8 roles


def get_all_available_tools() -> List[str]:
    """
    Get list of all available tools for agent configuration.
    
    Returns:
        List of tool names
    """
    return [
        "Gemini",
        "Vibes",
        "Lucid AI",
        "MCP Server",
        "NotebookLM",
    ]

