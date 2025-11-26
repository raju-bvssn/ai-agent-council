"""
Intelligent model selection engine for Agent Council.

Automatically selects the most appropriate Gemini model based on:
- Task complexity
- Context length requirements
- Required reasoning depth
- Agent role
- Keywords in the description

Ensures cost-effective model usage while maintaining quality.
"""

from typing import Optional
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Model configurations with capabilities
MODEL_CONFIGS = {
    "gemini-1.5-pro": {
        "context_window": 2000000,  # 2M tokens
        "cost_tier": "high",
        "best_for": ["complex_reasoning", "large_context", "architecture", "governance"],
        "description": "Most capable model for complex architectural decisions"
    },
    "gemini-1.5-pro-latest": {
        "context_window": 2000000,
        "cost_tier": "high",
        "best_for": ["security", "compliance", "policy", "critical_decisions"],
        "description": "Latest Pro model with enhanced security analysis"
    },
    "gemini-1.5-flash": {
        "context_window": 1000000,  # 1M tokens
        "cost_tier": "medium",
        "best_for": ["reviews", "feedback", "standard_tasks", "iteration"],
        "description": "Fast, efficient model for standard tasks"
    },
    "gemini-1.5-flash-8b": {
        "context_window": 1000000,
        "cost_tier": "low",
        "best_for": ["suggestions", "quick_analysis", "classification"],
        "description": "Lightweight model for simple tasks"
    }
}

# Default model
DEFAULT_MODEL = "gemini-1.5-flash"


def auto_select_model(
    description: str,
    agent_role: Optional[str] = None,
    context_length: Optional[int] = None
) -> str:
    """
    Intelligently select the most appropriate Gemini model.
    
    Selection criteria (in order of priority):
    1. Context length requirements
    2. Security/governance keywords → pro-latest
    3. Complexity keywords → pro
    4. Agent role → specialized selection
    5. Description length → pro for long descriptions
    6. Default → flash
    
    Args:
        description: Task description or requirements
        agent_role: Agent role identifier (e.g., "master", "security_reviewer")
        context_length: Estimated context length in tokens
        
    Returns:
        Model identifier string
    """
    desc_lower = description.lower()
    desc_length = len(description)
    
    # Log selection process
    logger.info(
        "model_selection_started",
        desc_length=desc_length,
        agent_role=agent_role,
        context_length=context_length
    )
    
    # 1. Context length requirements
    if context_length:
        if context_length > 1000000:
            logger.info("model_selected_by_context", model="gemini-1.5-pro", reason="large_context")
            return "gemini-1.5-pro"
    
    # 2. Security, governance, policy, compliance → pro-latest
    security_keywords = [
        "security", "governance", "policy", "compliance", "audit",
        "gdpr", "hipaa", "sox", "pci", "encryption", "authentication",
        "authorization", "vulnerability", "penetration", "threat"
    ]
    if any(keyword in desc_lower for keyword in security_keywords):
        logger.info("model_selected_by_keywords", model="gemini-1.5-pro-latest", reason="security_focus")
        return "gemini-1.5-pro-latest"
    
    # 3. Complex architectural keywords → pro
    architecture_keywords = [
        "architecture", "integration", "nfr", "high volume", "scalability",
        "distributed", "microservices", "enterprise", "multi-tenant",
        "performance optimization", "load balancing", "caching strategy",
        "disaster recovery", "high availability", "fault tolerance"
    ]
    if any(keyword in desc_lower for keyword in architecture_keywords):
        logger.info("model_selected_by_keywords", model="gemini-1.5-pro", reason="architecture_complexity")
        return "gemini-1.5-pro"
    
    # 4. Agent role-based selection
    if agent_role:
        role_lower = agent_role.lower()
        
        # Master Architect and Solution Architect → pro
        if "master" in role_lower or "solution_architect" in role_lower or "adjudicator" in role_lower:
            logger.info("model_selected_by_role", model="gemini-1.5-pro", role=agent_role)
            return "gemini-1.5-pro"
        
        # Security reviewer → pro-latest
        if "security" in role_lower:
            logger.info("model_selected_by_role", model="gemini-1.5-pro-latest", role=agent_role)
            return "gemini-1.5-pro-latest"
        
        # Suggestion engine, FAQ, simple tasks → flash-8b
        if any(keyword in role_lower for keyword in ["suggestion", "faq", "quick"]):
            logger.info("model_selected_by_role", model="gemini-1.5-flash-8b", role=agent_role)
            return "gemini-1.5-flash-8b"
    
    # 5. Description length → pro for very long descriptions
    if desc_length > 400:
        logger.info("model_selected_by_length", model="gemini-1.5-pro", length=desc_length)
        return "gemini-1.5-pro"
    
    # 6. Quick/simple task keywords → flash-8b
    simple_keywords = ["review", "feedback", "quick", "polish", "summary", "list"]
    if any(keyword in desc_lower for keyword in simple_keywords) and desc_length < 200:
        logger.info("model_selected_by_keywords", model="gemini-1.5-flash-8b", reason="simple_task")
        return "gemini-1.5-flash-8b"
    
    # 7. Default fallback
    logger.info("model_selected_default", model=DEFAULT_MODEL)
    return DEFAULT_MODEL


def get_model_info(model_name: str) -> dict:
    """
    Get configuration information for a model.
    
    Args:
        model_name: Model identifier
        
    Returns:
        Dict with model configuration
    """
    return MODEL_CONFIGS.get(model_name, {
        "context_window": 1000000,
        "cost_tier": "unknown",
        "best_for": [],
        "description": "Unknown model"
    })


def estimate_token_count(text: str) -> int:
    """
    Rough estimation of token count.
    
    Rule of thumb: ~4 characters per token for English text.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def validate_model_for_context(model_name: str, context_length: int) -> bool:
    """
    Validate that a model can handle the required context length.
    
    Args:
        model_name: Model identifier
        context_length: Required context length in tokens
        
    Returns:
        True if model can handle the context, False otherwise
    """
    config = get_model_info(model_name)
    max_context = config.get("context_window", 0)
    
    return context_length <= max_context


def select_model_with_override(
    description: str,
    agent_role: Optional[str] = None,
    context_length: Optional[int] = None,
    manual_override: Optional[str] = None,
    auto_mode: bool = True
) -> tuple[str, bool]:
    """
    Select model with support for manual override.
    
    Args:
        description: Task description
        agent_role: Agent role
        context_length: Context length requirement
        manual_override: Manually selected model (if any)
        auto_mode: Whether auto-selection is enabled
        
    Returns:
        Tuple of (selected_model, was_auto_selected)
    """
    # If manual override provided and auto_mode is False, use override
    if manual_override and not auto_mode:
        # Validate override is valid
        if manual_override in MODEL_CONFIGS:
            logger.info("model_manual_override", model=manual_override)
            return manual_override, False
        else:
            logger.warning("model_manual_override_invalid", model=manual_override)
    
    # Auto-select
    selected = auto_select_model(description, agent_role, context_length)
    return selected, True


def list_available_models() -> list[dict]:
    """
    List all available models with their configurations.
    
    Returns:
        List of model configurations
    """
    return [
        {
            "name": name,
            **config
        }
        for name, config in MODEL_CONFIGS.items()
    ]

