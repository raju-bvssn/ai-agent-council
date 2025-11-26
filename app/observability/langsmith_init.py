"""
LangSmith initialization and tracing configuration.

Provides centralized LangSmith client initialization and environment setup
for observability across agents, tools, workflows, and API endpoints.
"""

import os
from typing import Optional
from functools import lru_cache

from app.utils.logging import get_logger
from app.utils.settings import get_settings

logger = get_logger(__name__)

# Global client instance (lazy-loaded)
_langsmith_client: Optional[any] = None
_initialization_attempted = False


def initialize_langsmith() -> Optional[any]:
    """
    Initialize LangSmith tracing and return client instance.
    
    Sets up environment variables required for LangChain/LangSmith tracing
    and creates a LangSmith client if enabled in settings.
    
    Returns:
        LangSmith Client instance if enabled and API key available, None otherwise
    """
    global _langsmith_client, _initialization_attempted
    
    # Only attempt initialization once
    if _initialization_attempted:
        return _langsmith_client
    
    _initialization_attempted = True
    settings = get_settings()
    
    # Check if tracing is enabled
    if not settings.is_langsmith_enabled:
        logger.info("langsmith_disabled", reason="enable_langsmith=False in settings")
        return None
    
    # Get API key
    api_key = settings.get_langsmith_api_key()
    if not api_key:
        logger.warning(
            "langsmith_no_api_key",
            reason="LangSmith enabled but no API key found",
            hint="Set LANGSMITH_API_KEY or LANGCHAIN_API_KEY environment variable"
        )
        return None
    
    try:
        # Import LangSmith (lazy import to avoid dependency if not used)
        try:
            from langsmith import Client
        except ImportError:
            logger.error(
                "langsmith_import_error",
                reason="langsmith package not installed",
                hint="Install with: pip install langsmith"
            )
            return None
        
        # Set environment variables for LangChain tracing
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
        
        # Create client
        _langsmith_client = Client(
            api_key=api_key,
            api_url=settings.langsmith_endpoint
        )
        
        logger.info(
            "langsmith_initialized",
            project=settings.langsmith_project,
            endpoint=settings.langsmith_endpoint
        )
        
        return _langsmith_client
        
    except Exception as e:
        logger.error(
            "langsmith_initialization_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        return None


@lru_cache
def get_langsmith_client() -> Optional[any]:
    """
    Get the LangSmith client instance (cached).
    
    Lazy-loads the client on first call. Safe to call multiple times.
    
    Returns:
        LangSmith Client instance or None if not initialized
    """
    global _langsmith_client
    
    if _langsmith_client is None:
        _langsmith_client = initialize_langsmith()
    
    return _langsmith_client


def is_tracing_enabled() -> bool:
    """
    Check if LangSmith tracing is enabled and configured.
    
    Returns:
        True if tracing is enabled and client is initialized
    """
    settings = get_settings()
    
    if not settings.is_langsmith_enabled:
        return False
    
    if not settings.get_langsmith_api_key():
        return False
    
    # Try to get client (will initialize if not done yet)
    client = get_langsmith_client()
    return client is not None


def get_trace_url(run_id: str) -> str:
    """
    Generate LangSmith UI URL for a given run ID.
    
    Args:
        run_id: The LangSmith run ID
        
    Returns:
        Full URL to view the trace in LangSmith UI
    """
    settings = get_settings()
    project = settings.langsmith_project
    
    # LangSmith UI URL format
    return f"https://smith.langchain.com/public/{project}/r/{run_id}"


def get_current_run_id() -> Optional[str]:
    """
    Get the current LangSmith run ID from tracing context.
    
    Returns:
        Current run ID if in a traced context, None otherwise
    """
    if not is_tracing_enabled():
        return None
    
    try:
        from langchain_core.tracers.context import get_run_tree
        
        run_tree = get_run_tree()
        if run_tree:
            return str(run_tree.id)
        
        return None
        
    except ImportError:
        logger.warning("langchain_core_not_available", hint="Install langchain-core for run context")
        return None
    except Exception as e:
        logger.debug("get_current_run_id_failed", error=str(e))
        return None


# Initialize on module import (but lazy - won't fail if disabled)
# This ensures tracing is set up before any traced code runs
if get_settings().is_langsmith_enabled:
    initialize_langsmith()

