"""
Application settings and configuration.

Uses Pydantic Settings for type-safe configuration with environment variable support.
Follows the Single Responsibility Principle by separating concerns into logical groups.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings loaded from environment variables.

    All sensitive values should be stored in .env file (not committed to git).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    env: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="API auto-reload on code changes")
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Full backend API URL (for Streamlit UI to connect)"
    )
    secret_key: str = Field(default="change-me-in-production", description="Secret key for JWT/sessions")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8501,*",
        description="Comma-separated CORS allowed origins"
    )
    
    # Deployment Configuration
    demo_mode: bool = Field(
        default=False,
        description="Enable demo mode with mock tool responses (no external API calls)"
    )
    health_check_enabled: bool = Field(default=True, description="Enable /health endpoint")

    # LLM Provider (Google Gemini - Mission Critical Data Compliant)
    google_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", description="Gemini model name")
    gemini_temperature: float = Field(default=0.7, description="LLM temperature", ge=0.0, le=2.0)
    gemini_max_tokens: int = Field(default=8192, description="Max output tokens", gt=0)

    # LangSmith Tracing
    langchain_tracing_v2: bool = Field(default=False, description="Enable LangSmith tracing")
    langchain_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    langchain_project: str = Field(default="agent-council", description="LangSmith project name")

    # Tool Integration
    vibes_api_key: Optional[str] = Field(default=None, description="MuleSoft Vibes API key")
    vibes_base_url: str = Field(
        default="https://vibes.mulesoft.com/api",
        description="Vibes API base URL"
    )
    mcp_server_url: Optional[str] = Field(default=None, description="MCP Server URL")
    mcp_api_key: Optional[str] = Field(default=None, description="MCP Server API key")
    notebooklm_api_key: Optional[str] = Field(default=None, description="NotebookLM API key")
    lucid_api_key: Optional[str] = Field(default=None, description="Lucid AI API key")

    # Database
    database_url: str = Field(
        default="sqlite:///./agent_council.db",
        description="Database connection URL"
    )

    # UI Configuration
    streamlit_port: int = Field(default=8501, description="Streamlit UI port")
    streamlit_theme: str = Field(default="dark", description="Streamlit theme")

    # Rate Limiting & Retries
    max_retries: int = Field(default=3, description="Max retry attempts for API calls", ge=0)
    retry_delay: float = Field(default=1.0, description="Delay between retries (seconds)", ge=0)
    request_timeout: int = Field(default=30, description="Request timeout (seconds)", gt=0)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"env must be one of {valid_envs}")
        return v_lower

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == "development"
    
    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode (mock tool responses)."""
        return self.demo_mode

    def get_allowed_origins_list(self) -> list[str]:
        """Parse comma-separated allowed origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
    
    def get_api_base_url(self) -> str:
        """
        Get the API base URL for frontend-to-backend communication.
        
        Priority:
        1. Explicitly set api_base_url
        2. Constructed from api_host and api_port
        
        Returns:
            Full API base URL
        """
        if self.api_base_url and self.api_base_url != "http://localhost:8000":
            return self.api_base_url.rstrip("/")
        
        # Construct from host and port
        protocol = "https" if self.is_production else "http"
        host = self.api_host if self.api_host != "0.0.0.0" else "localhost"
        return f"{protocol}://{host}:{self.api_port}"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    Call this function to access settings throughout the application.

    Returns:
        Settings instance
    """
    return Settings()

