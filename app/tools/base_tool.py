"""
Base tool client with common functionality.

All tool clients inherit from BaseTool to ensure consistent
error handling, retries, timeouts, and logging.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from functools import wraps

from app.tools.schemas import ToolResult, ToolError
from app.utils.logging import get_logger
from app.utils.exceptions import ToolException


logger = get_logger(__name__)


def with_timeout(seconds: int = 30):
    """
    Decorator to add timeout protection to tool methods.
    
    Args:
        seconds: Maximum execution time in seconds
        
    Raises:
        ToolException: If execution exceeds timeout
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error("tool_timeout", func=func.__name__, timeout=seconds)
                raise ToolException(f"Tool execution timed out after {seconds}s")
        return wrapper
    return decorator


def with_retry(max_attempts: int = 3, backoff_factor: float = 1.5):
    """
    Decorator to add retry logic to tool methods.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        
    The decorator will retry on any exception, with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            "tool_retry",
                            func=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            wait_time=wait_time,
                            error=str(e)
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            "tool_max_retries_exceeded",
                            func=func.__name__,
                            max_attempts=max_attempts,
                            error=str(e)
                        )
            raise last_exception
        return wrapper
    return decorator


class BaseTool(ABC):
    """
    Abstract base class for all tool clients.
    
    Provides common functionality:
    - Consistent error handling
    - Timeout protection
    - Retry logic
    - Structured logging
    - Standard result format
    
    Subclasses must implement:
    - name: Tool identifier
    - _execute: Core tool logic
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base tool with optional configuration.
        
        Args:
            config: Tool-specific configuration (API keys, URLs, etc.)
        """
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool's identifier (e.g., 'vibes', 'mcp', 'lucid')."""
        pass
    
    @abstractmethod
    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the core tool logic.
        
        This method must be implemented by each tool client.
        
        Args:
            operation: Specific operation to perform
            parameters: Operation parameters
            
        Returns:
            ToolResult with success status and data
            
        Raises:
            ToolException: On execution failure
        """
        pass
    
    async def execute(
        self,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Public execution method with error handling and logging.
        
        Args:
            operation: Operation to perform
            parameters: Operation parameters
            context: Additional context from workflow
            
        Returns:
            ToolResult with execution outcome
        """
        params = parameters or {}
        self.logger.info(
            "tool_execute_start",
            tool=self.name,
            operation=operation,
            has_context=context is not None
        )
        
        try:
            result = await self._execute(operation, params)
            
            self.logger.info(
                "tool_execute_success",
                tool=self.name,
                operation=operation,
                success=result.success
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "tool_execute_failed",
                tool=self.name,
                operation=operation,
                error=str(e)
            )
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                summary=f"Tool execution failed: {str(e)}",
                error=ToolError(
                    error_type=type(e).__name__,
                    message=str(e),
                    details={"operation": operation, "parameters": params}
                )
            )
    
    def _create_success_result(
        self,
        summary: str,
        details: Optional[Dict[str, Any]] = None,
        artifacts: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Helper to create a successful ToolResult.
        
        Args:
            summary: Brief description of the result
            details: Detailed data
            artifacts: List of URLs or file paths
            metadata: Additional metadata
            
        Returns:
            ToolResult with success=True
        """
        return ToolResult(
            tool_name=self.name,
            success=True,
            summary=summary,
            details=details or {},
            artifacts=artifacts,
            metadata=metadata or {}
        )
    
    def _create_error_result(
        self,
        error_message: str,
        error_type: str = "ToolError",
        details: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Helper to create a failed ToolResult.
        
        Args:
            error_message: Description of the error
            error_type: Classification of the error
            details: Additional error context
            
        Returns:
            ToolResult with success=False
        """
        return ToolResult(
            tool_name=self.name,
            success=False,
            summary=f"Error: {error_message}",
            error=ToolError(
                error_type=error_type,
                message=error_message,
                details=details
            )
        )

