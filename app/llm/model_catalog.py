"""
Model catalog for Agent Council system.

Defines available LLM models and their capabilities.
Only includes Mission Critical Data compliant models (Google Gemini).
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ModelCapability(Enum):
    """Model capabilities enum."""
    TEXT_GENERATION = "text_generation"
    JSON_MODE = "json_mode"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    LONG_CONTEXT = "long_context"


@dataclass
class ModelInfo:
    """
    Model information and capabilities.

    Attributes:
        name: Model identifier
        display_name: Human-readable name
        provider: Provider name
        max_tokens: Maximum output tokens
        context_window: Maximum context window size
        capabilities: List of model capabilities
        recommended_temperature: Recommended temperature for this model
        cost_per_1k_tokens: Estimated cost per 1K tokens (for tracking)
    """
    name: str
    display_name: str
    provider: str
    max_tokens: int
    context_window: int
    capabilities: list[ModelCapability]
    recommended_temperature: float = 0.7
    cost_per_1k_tokens: float = 0.0


# Google Gemini Models (Mission Critical Data Compliant)
GEMINI_MODELS = {
    "gemini-2.0-flash-exp": ModelInfo(
        name="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash (Experimental)",
        provider="google",
        max_tokens=8192,
        context_window=1048576,  # 1M tokens
        capabilities=[
            ModelCapability.TEXT_GENERATION,
            ModelCapability.JSON_MODE,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
        recommended_temperature=0.7,
        cost_per_1k_tokens=0.0,  # Check current pricing
    ),
    "gemini-1.5-pro": ModelInfo(
        name="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        provider="google",
        max_tokens=8192,
        context_window=2097152,  # 2M tokens
        capabilities=[
            ModelCapability.TEXT_GENERATION,
            ModelCapability.JSON_MODE,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
        recommended_temperature=0.7,
        cost_per_1k_tokens=0.0,
    ),
    "gemini-1.5-flash": ModelInfo(
        name="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        provider="google",
        max_tokens=8192,
        context_window=1048576,
        capabilities=[
            ModelCapability.TEXT_GENERATION,
            ModelCapability.JSON_MODE,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
        recommended_temperature=0.7,
        cost_per_1k_tokens=0.0,
    ),
    "gemini-flash-latest": ModelInfo(
        name="gemini-flash-latest",
        display_name="Gemini Flash (Latest Stable)",
        provider="google",
        max_tokens=8192,
        context_window=1048576,
        capabilities=[
            ModelCapability.TEXT_GENERATION,
            ModelCapability.JSON_MODE,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
        recommended_temperature=0.7,
        cost_per_1k_tokens=0.0,
    ),
    "gemini-pro-latest": ModelInfo(
        name="gemini-pro-latest",
        display_name="Gemini Pro (Latest Stable)",
        provider="google",
        max_tokens=8192,
        context_window=2097152,
        capabilities=[
            ModelCapability.TEXT_GENERATION,
            ModelCapability.JSON_MODE,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
        recommended_temperature=0.7,
        cost_per_1k_tokens=0.0,
    ),
}


class ModelCatalog:
    """
    Catalog of available models.

    Provides utilities for model selection and validation.
    """

    @staticmethod
    def get_model(model_name: str) -> ModelInfo:
        """
        Get model info by name.

        Args:
            model_name: Model identifier

        Returns:
            ModelInfo object

        Raises:
            ValueError: If model not found
        """
        if model_name in GEMINI_MODELS:
            return GEMINI_MODELS[model_name]
        raise ValueError(f"Model '{model_name}' not found in catalog")

    @staticmethod
    def list_models(provider: Optional[str] = None) -> List[ModelInfo]:
        """
        List all available models.

        Args:
            provider: Filter by provider (optional)

        Returns:
            List of ModelInfo objects
        """
        all_models = list(GEMINI_MODELS.values())

        if provider:
            all_models = [m for m in all_models if m.provider == provider]

        return all_models

    @staticmethod
    def get_default_model() -> ModelInfo:
        """
        Get the default model for Agent Council.

        Returns:
            Default ModelInfo
        """
        return GEMINI_MODELS["gemini-2.0-flash-exp"]

    @staticmethod
    def supports_capability(model_name: str, capability: ModelCapability) -> bool:
        """
        Check if model supports a specific capability.

        Args:
            model_name: Model identifier
            capability: Capability to check

        Returns:
            True if supported, False otherwise
        """
        try:
            model = ModelCatalog.get_model(model_name)
            return capability in model.capabilities
        except ValueError:
            return False

