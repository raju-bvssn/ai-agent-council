"""
LLM provider implementations for Agent Council system.

Only implements Google Gemini provider (Mission Critical Data compliant).
Follows Open/Closed Principle: extend for additional providers via base class.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.llm.model_catalog import ModelCatalog
from app.utils.exceptions import (
    LLMProviderException,
    LLMRateLimitException,
    LLMSafetyException,
    LLMTimeoutException,
)
from app.utils.logging import get_logger
from app.utils.settings import get_settings

logger = get_logger(__name__)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implements Dependency Inversion Principle: depend on abstraction, not concrete impl.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (optional)
            max_tokens: Maximum output tokens (optional)
            json_mode: Force JSON output (optional)

        Returns:
            Generated text

        Raises:
            LLMProviderException: On provider errors
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name being used."""
        pass


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider.

    Mission Critical Data compliant provider with safety filters and retry logic.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key (uses settings if not provided)
            model_name: Model name (uses settings if not provided)
            temperature: Default temperature (uses settings if not provided)
            max_tokens: Default max tokens (uses settings if not provided)
        """
        settings = get_settings()

        self.api_key = api_key or settings.google_api_key
        if not self.api_key:
            raise LLMProviderException(
                "Google API key not configured",
                details={"config_key": "GOOGLE_API_KEY"}
            )

        self.model_name = model_name or settings.gemini_model
        self.temperature = temperature or settings.gemini_temperature
        self.max_tokens = max_tokens or settings.gemini_max_tokens

        # Validate model exists in catalog
        try:
            self.model_info = ModelCatalog.get_model(self.model_name)
        except ValueError as e:
            raise LLMProviderException(str(e))

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model_name)

        logger.info(
            "gemini_provider_initialized",
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

    def get_model_name(self) -> str:
        """Get the model name being used."""
        return self.model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate text completion using Gemini.

        Implements retry logic with exponential backoff.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (optional)
            max_tokens: Maximum output tokens (optional)
            json_mode: Force JSON output (optional)

        Returns:
            Generated text

        Raises:
            LLMProviderException: On provider errors
            LLMRateLimitException: On rate limit errors
            LLMSafetyException: On safety filter violations
            LLMTimeoutException: On timeout errors
        """
        try:
            # Build generation config
            generation_config = {
                "temperature": temperature or self.temperature,
                "max_output_tokens": max_tokens or self.max_tokens,
            }

            if json_mode:
                generation_config["response_mime_type"] = "application/json"

            # Build full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            logger.debug(
                "gemini_generate_request",
                model=self.model_name,
                prompt_length=len(full_prompt),
                json_mode=json_mode
            )

            # Generate
            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings={
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
                }
            )

            # Check for safety blocks
            if not response.candidates:
                raise LLMSafetyException(
                    "Content was blocked by safety filters",
                    details={"prompt_length": len(full_prompt)}
                )

            result = response.text

            logger.info(
                "gemini_generate_success",
                model=self.model_name,
                output_length=len(result)
            )

            return result

        except Exception as e:
            error_msg = str(e).lower()

            if "quota" in error_msg or "rate limit" in error_msg:
                logger.error("gemini_rate_limit", error=str(e))
                raise LLMRateLimitException(
                    "Gemini API rate limit exceeded",
                    details={"error": str(e)}
                )
            elif "timeout" in error_msg:
                logger.error("gemini_timeout", error=str(e))
                raise LLMTimeoutException(
                    "Gemini API request timeout",
                    details={"error": str(e)}
                )
            elif "safety" in error_msg or "blocked" in error_msg:
                logger.error("gemini_safety_block", error=str(e))
                raise LLMSafetyException(
                    "Content blocked by Gemini safety filters",
                    details={"error": str(e)}
                )
            else:
                logger.error("gemini_provider_error", error=str(e))
                raise LLMProviderException(
                    f"Gemini API error: {str(e)}",
                    details={"error": str(e)}
                )

