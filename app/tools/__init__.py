"""
Tools package for Agent Council system.

Provides integrations with external tools:
- MuleSoft Vibes (code generation, flow validation)
- MCP Server (platform metadata, deployment config)
- NotebookLM (summarization, evidence extraction)
- Lucid AI (diagram generation)
- AI Chain (additional AI utilities)
"""

from app.tools.ai_chain import AIChainClient, get_ai_chain_client
from app.tools.lucid_diagrams import LucidAIClient, get_lucid_client
from app.tools.mcp_server import MCPServerClient, get_mcp_client
from app.tools.notebooklm import NotebookLMClient, get_notebooklm_client
from app.tools.vibes import VibesClient, get_vibes_client

__all__ = [
    # Vibes
    "VibesClient",
    "get_vibes_client",
    # MCP Server
    "MCPServerClient",
    "get_mcp_client",
    # NotebookLM
    "NotebookLMClient",
    "get_notebooklm_client",
    # Lucid AI
    "LucidAIClient",
    "get_lucid_client",
    # AI Chain
    "AIChainClient",
    "get_ai_chain_client",
]

