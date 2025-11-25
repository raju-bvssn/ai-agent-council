"""
Tool integration package for Agent Council.

This package contains clients for external tools used by agents:
- Vibes: MuleSoft best practice analysis
- MCP Server: Platform metadata and configuration
- Lucid AI: Diagram generation
- Gemini: Large-context reasoning
- NotebookLM: Grounded summaries and evidence-based analysis
"""

from app.tools.schemas import ToolResult, ToolError
from app.tools.tool_registry import get_tool, list_available_tools, TOOL_REGISTRY

__all__ = [
    "ToolResult",
    "ToolError",
    "get_tool",
    "list_available_tools",
    "TOOL_REGISTRY",
]
