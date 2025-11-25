"""
Custom exceptions for the Agent Council system.

This module defines domain-specific exceptions following Clean Architecture principles.
All exceptions inherit from a base AgentCouncilException for centralized error handling.
"""

from typing import Any, Optional


class AgentCouncilException(Exception):
    """Base exception for all Agent Council errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """
        Initialize base exception.

        Args:
            message: Human-readable error message
            details: Additional context for debugging (will be sanitized in logs)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


# LLM Provider Exceptions
class LLMProviderException(AgentCouncilException):
    """Raised when LLM provider operations fail."""
    pass


class LLMSafetyException(AgentCouncilException):
    """Raised when content violates safety policies."""
    pass


class LLMRateLimitException(AgentCouncilException):
    """Raised when LLM rate limits are exceeded."""
    pass


class LLMTimeoutException(AgentCouncilException):
    """Raised when LLM requests timeout."""
    pass


# Agent Exceptions
class AgentExecutionException(AgentCouncilException):
    """Raised when agent execution fails."""
    pass


class AgentValidationException(AgentCouncilException):
    """Raised when agent input/output validation fails."""
    pass


# Workflow Exceptions
class WorkflowException(AgentCouncilException):
    """Raised when workflow execution fails."""
    pass


class StateTransitionException(AgentCouncilException):
    """Raised when state machine transitions fail."""
    pass


# Tool Exceptions
class ToolException(AgentCouncilException):
    """Base exception for tool-related errors."""
    pass


class VibesException(ToolException):
    """Raised when Vibes API operations fail."""
    pass


class MCPServerException(ToolException):
    """Raised when MCP Server operations fail."""
    pass


class NotebookLMException(ToolException):
    """Raised when NotebookLM operations fail."""
    pass


class LucidAIException(ToolException):
    """Raised when Lucid AI operations fail."""
    pass


# Data & Persistence Exceptions
class PersistenceException(AgentCouncilException):
    """Raised when data persistence operations fail."""
    pass


class SessionNotFoundException(AgentCouncilException):
    """Raised when session cannot be found."""
    pass


# Configuration Exceptions
class ConfigurationException(AgentCouncilException):
    """Raised when configuration is invalid or missing."""
    pass


# Security Exceptions
class SecurityException(AgentCouncilException):
    """Raised when security violations are detected."""
    pass


class PromptInjectionException(SecurityException):
    """Raised when potential prompt injection is detected."""
    pass


class UnauthorizedAccessException(SecurityException):
    """Raised when unauthorized access is attempted."""
    pass

