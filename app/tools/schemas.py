"""
Standard schemas for tool results and responses.

All tool clients must return ToolResult instances for consistency
and structured error handling.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolError(BaseModel):
    """
    Represents an error that occurred during tool execution.
    
    Attributes:
        error_type: Classification of the error (e.g., "timeout", "auth_error")
        message: Human-readable error description
        details: Additional context about the error
    """
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ToolResult(BaseModel):
    """
    Standard response format for all tool executions.
    
    This ensures consistency across all tool integrations and allows
    agents to process tool outputs uniformly.
    
    Attributes:
        tool_name: Identifier for the tool (e.g., "vibes", "mcp", "lucid")
        success: Whether the tool execution succeeded
        summary: Brief summary of the tool's output
        details: Detailed structured data from the tool
        artifacts: List of URLs, file paths, or identifiers (e.g., diagram links)
        error: Error information if success=False
        metadata: Additional metadata (execution time, API version, etc.)
    """
    tool_name: str
    success: bool
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    artifacts: Optional[List[str]] = Field(default=None)
    error: Optional[ToolError] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "vibes",
                "success": True,
                "summary": "API design follows MuleSoft best practices",
                "details": {
                    "score": 95,
                    "recommendations": ["Use async patterns for long-running operations"]
                },
                "artifacts": ["https://vibes.mulesoft.com/report/abc123"],
                "metadata": {
                    "execution_time_ms": 1250,
                    "api_version": "v2"
                }
            }
        }


class ToolRequest(BaseModel):
    """
    Standard request format for tool invocations.
    
    Attributes:
        tool_name: Which tool to invoke
        operation: Specific operation/method to call
        parameters: Parameters for the operation
        context: Additional context from the workflow
    """
    tool_name: str
    operation: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = None

