"""
Tool Registry for centralized tool management.

Provides a single source of truth for all available tools and their
configurations. Agents query this registry to access tool clients.
"""

from typing import Any, Dict, List, Optional

from app.tools.base_tool import BaseTool
from app.tools.vibes_client import VibesClient
from app.tools.mcp_client import MCPClient
from app.tools.lucid_client import LucidClient
from app.tools.gemini_client import GeminiClient
from app.tools.notebooklm_client import NotebookLMClient
from app.utils.logging import get_logger
from app.utils.exceptions import ToolException


logger = get_logger(__name__)


# Global tool registry
_TOOL_INSTANCES: Dict[str, BaseTool] = {}
_INITIALIZED = False


def _initialize_registry(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize the tool registry with tool instances.
    
    Args:
        config: Optional configuration dict with tool-specific configs
    """
    global _TOOL_INSTANCES, _INITIALIZED
    
    if _INITIALIZED:
        logger.debug("tool_registry_already_initialized")
        return
    
    config = config or {}
    
    try:
        _TOOL_INSTANCES = {
            "vibes": VibesClient(config.get("vibes")),
            "mcp": MCPClient(config.get("mcp")),
            "lucid": LucidClient(config.get("lucid")),
            "gemini": GeminiClient(config.get("gemini")),
            "notebooklm": NotebookLMClient(config.get("notebooklm")),
        }
        
        _INITIALIZED = True
        logger.info(
            "tool_registry_initialized",
            tools=list(_TOOL_INSTANCES.keys())
        )
        
    except Exception as e:
        logger.error("tool_registry_initialization_failed", error=str(e))
        raise ToolException(f"Failed to initialize tool registry: {str(e)}")


def get_tool(tool_name: str) -> BaseTool:
    """
    Retrieve a tool client by name.
    
    Args:
        tool_name: Identifier of the tool (e.g., "vibes", "mcp", "lucid")
        
    Returns:
        The tool client instance
        
    Raises:
        ToolException: If tool not found or registry not initialized
    """
    if not _INITIALIZED:
        _initialize_registry()
    
    tool = _TOOL_INSTANCES.get(tool_name.lower())
    
    if not tool:
        available = list(_TOOL_INSTANCES.keys())
        logger.error("tool_not_found", tool=tool_name, available=available)
        raise ToolException(
            f"Tool '{tool_name}' not found. Available tools: {available}"
        )
    
    logger.debug("tool_retrieved", tool=tool_name)
    return tool


def list_available_tools() -> List[str]:
    """
    List all available tool names.
    
    Returns:
        List of tool identifiers
    """
    if not _INITIALIZED:
        _initialize_registry()
    
    return list(_TOOL_INSTANCES.keys())


def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """
    Get information about a specific tool.
    
    Args:
        tool_name: Tool identifier
        
    Returns:
        Dict with tool metadata
        
    Raises:
        ToolException: If tool not found
    """
    tool = get_tool(tool_name)
    
    return {
        "name": tool.name,
        "class": tool.__class__.__name__,
        "description": tool.__class__.__doc__.strip() if tool.__class__.__doc__ else "No description",
        "config_keys": list(tool.config.keys()) if tool.config else []
    }


def reinitialize_registry(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Reinitialize the tool registry with new configuration.
    
    Useful for testing or dynamic configuration changes.
    
    Args:
        config: New configuration dict
    """
    global _INITIALIZED
    
    logger.info("tool_registry_reinitializing")
    _INITIALIZED = False
    _initialize_registry(config)


# Tool registry metadata for UI and documentation
TOOL_REGISTRY = {
    "vibes": {
        "display_name": "Vibes",
        "full_name": "MuleSoft Vibes",
        "category": "Integration Analysis",
        "description": "MuleSoft best practice analysis and pattern recommendations",
        "capabilities": [
            "API specification validation",
            "Integration pattern recommendations",
            "Error handling review",
            "NFR validation"
        ],
        "typical_users": [
            "Solution Architect",
            "Integration Pattern Advisor",
            "Security Reviewer"
        ]
    },
    "mcp": {
        "display_name": "MCP Server",
        "full_name": "MuleSoft Control Plane",
        "category": "Platform Metadata",
        "description": "Platform configuration and deployment information",
        "capabilities": [
            "Environment details",
            "API Manager metadata",
            "Policy management",
            "Runtime configuration",
            "Client application registry"
        ],
        "typical_users": [
            "Platform Throughput Analyst",
            "Security Reviewer",
            "Cost Optimization Agent"
        ]
    },
    "lucid": {
        "display_name": "Lucid AI",
        "full_name": "Lucid AI Diagram Generator",
        "category": "Visualization",
        "description": "Architecture and sequence diagram generation",
        "capabilities": [
            "Architecture diagrams",
            "Sequence diagrams",
            "Data flow diagrams",
            "Integration flow diagrams"
        ],
        "typical_users": [
            "Solution Architect",
            "Final Architect Agent"
        ]
    },
    "gemini": {
        "display_name": "Gemini",
        "full_name": "Google Gemini LLM",
        "category": "Reasoning",
        "description": "Large-context reasoning and structured analysis",
        "capabilities": [
            "General text generation",
            "Long-context analysis",
            "Structured reasoning",
            "Summarization",
            "Insight extraction"
        ],
        "typical_users": [
            "All agents (fallback/core reasoning)"
        ]
    },
    "notebooklm": {
        "display_name": "NotebookLM",
        "full_name": "NotebookLM Grounded Analysis",
        "category": "Evidence-Based Analysis",
        "description": "Grounded summaries with source citations",
        "capabilities": [
            "Summarization with citations",
            "Evidence-based question answering",
            "Multi-document synthesis",
            "Claim verification"
        ],
        "typical_users": [
            "FAQ Agent",
            "Master Architect",
            "All reviewers"
        ]
    }
}


def get_tool_metadata(tool_name: str) -> Dict[str, Any]:
    """
    Get display metadata for a tool.
    
    Args:
        tool_name: Tool identifier
        
    Returns:
        Dict with display metadata
        
    Raises:
        ToolException: If tool not found
    """
    metadata = TOOL_REGISTRY.get(tool_name.lower())
    
    if not metadata:
        available = list(TOOL_REGISTRY.keys())
        raise ToolException(
            f"Tool metadata for '{tool_name}' not found. Available: {available}"
        )
    
    return metadata


def get_all_tool_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Get metadata for all tools.
    
    Returns:
        Dict mapping tool names to their metadata
    """
    return TOOL_REGISTRY.copy()

