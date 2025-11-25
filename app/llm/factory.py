"""
LLM provider factory for Agent Council system.

Implements Factory Pattern for provider instantiation.
"""

from typing import Optional

from app.llm.providers import GeminiProvider, LLMProvider
from app.utils.exceptions import ConfigurationException
from app.utils.logging import get_logger
from app.utils.settings import get_settings

logger = get_logger(__name__)


class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.

    Implements Factory Pattern and Dependency Injection.
    """

    @staticmethod
    def create_provider(
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> LLMProvider:
        """
        Create LLM provider instance.

        Args:
            provider_name: Provider name (currently only 'google' supported)
            model_name: Model name (optional, uses default from settings)
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMProvider instance

        Raises:
            ConfigurationException: If provider not supported
        """
        settings = get_settings()

        # Default to Google Gemini (Mission Critical Data compliant)
        provider_name = provider_name or "google"

        if provider_name.lower() == "google":
            logger.info(
                "creating_gemini_provider",
                model=model_name or settings.gemini_model
            )
            return GeminiProvider(
                model_name=model_name,
                **kwargs
            )
        else:
            raise ConfigurationException(
                f"Unsupported LLM provider: {provider_name}. "
                f"Only 'google' (Gemini) is supported for Mission Critical Data compliance.",
                details={"provider": provider_name}
            )

    @staticmethod
    def create_default_provider() -> LLMProvider:
        """
        Create default LLM provider.

        Returns:
            Default LLMProvider (Gemini)
        """
        return LLMProviderFactory.create_provider()


# Convenience function
def get_llm_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs,
) -> LLMProvider:
    """
    Get LLM provider instance.

    Args:
        provider_name: Provider name (optional)
        model_name: Model name (optional)
        **kwargs: Additional provider-specific arguments

    Returns:
        LLMProvider instance
    """
    return LLMProviderFactory.create_provider(
        provider_name=provider_name,
        model_name=model_name,
        **kwargs
    )

