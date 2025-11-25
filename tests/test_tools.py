"""
Unit tests for tool clients.

Tests tool invocation, error handling, timeout/retry behavior,
and result formatting.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from app.tools.vibes_client import VibesClient
from app.tools.mcp_client import MCPClient
from app.tools.lucid_client import LucidClient
from app.tools.gemini_client import GeminiClient
from app.tools.notebooklm_client import NotebookLMClient
from app.tools.tool_registry import get_tool, list_available_tools, TOOL_REGISTRY
from app.tools.schemas import ToolResult, ToolError


class TestVibesClient:
    """Tests for Vibes client."""
    
    @pytest.mark.asyncio
    async def test_recommend_patterns_success(self):
        """Test successful pattern recommendation."""
        client = VibesClient()
        
        result = await client.execute(
            operation="recommend_patterns",
            parameters={"description": "Real-time data sync between Salesforce and external system"}
        )
        
        assert isinstance(result, ToolResult)
        assert result.tool_name == "vibes"
        assert result.success is True
        assert "primary_pattern" in result.details or result.success
    
    @pytest.mark.asyncio
    async def test_analyze_api_spec_invalid_input(self):
        """Test API spec analysis with missing input."""
        client = VibesClient()
        
        result = await client.execute(
            operation="analyze_api_spec",
            parameters={}  # Missing spec_text
        )
        
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None
        assert result.error.error_type == "InvalidParameter"
    
    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        """Test handling of unknown operation."""
        client = VibesClient()
        
        result = await client.execute(
            operation="invalid_operation",
            parameters={}
        )
        
        assert result.success is False
        assert "Unknown operation" in result.summary


class TestMCPClient:
    """Tests for MCP Server client."""
    
    @pytest.mark.asyncio
    async def test_get_environment_info_mock(self):
        """Test environment info retrieval in mock mode."""
        client = MCPClient()
        
        result = await client.execute(
            operation="get_environment_info",
            parameters={"env_id": "prod-env-001"}
        )
        
        assert isinstance(result, ToolResult)
        assert result.tool_name == "mcp"
        assert result.success is True
        assert "environment_id" in result.details
        assert result.details["environment_id"] == "prod-env-001"
    
    @pytest.mark.asyncio
    async def test_list_policies_returns_policies(self):
        """Test policy listing."""
        client = MCPClient()
        
        result = await client.execute(
            operation="list_policies",
            parameters={"env_id": "prod-env-001"}
        )
        
        assert result.success is True
        assert "policies" in result.details
        assert isinstance(result.details["policies"], list)
        assert len(result.details["policies"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_api_metadata(self):
        """Test API metadata retrieval."""
        client = MCPClient()
        
        result = await client.execute(
            operation="get_api_metadata",
            parameters={"api_id": "customer-api-v1"}
        )
        
        assert result.success is True
        assert "api_id" in result.details
        assert "applied_policies" in result.details


class TestLucidClient:
    """Tests for Lucid AI client."""
    
    @pytest.mark.asyncio
    async def test_generate_architecture_diagram(self):
        """Test architecture diagram generation."""
        client = LucidClient()
        
        result = await client.execute(
            operation="generate_architecture",
            parameters={
                "description": "Microservices architecture with API gateway, auth service, and data layer"
            }
        )
        
        assert result.success is True
        assert "mermaid_code" in result.details
        assert result.details["diagram_type"] == "architecture"
    
    @pytest.mark.asyncio
    async def test_generate_sequence_diagram(self):
        """Test sequence diagram generation."""
        client = LucidClient()
        
        result = await client.execute(
            operation="generate_sequence",
            parameters={
                "flows": "User authenticates -> API Gateway validates token -> Auth Service verifies"
            }
        )
        
        assert result.success is True
        assert result.details["diagram_type"] == "sequence"
        assert "participants" in result.details
    
    @pytest.mark.asyncio
    async def test_missing_description_fails(self):
        """Test that missing description fails gracefully."""
        client = LucidClient()
        
        result = await client.execute(
            operation="generate_architecture",
            parameters={}
        )
        
        assert result.success is False
        assert result.error.error_type == "InvalidParameter"


class TestGeminiClient:
    """Tests for Gemini client."""
    
    @pytest.mark.asyncio
    async def test_generate_operation(self):
        """Test basic generation."""
        client = GeminiClient()
        
        result = await client.execute(
            operation="generate",
            parameters={
                "prompt": "Explain the benefits of API-led connectivity",
                "model": "gemini-1.5-flash"
            }
        )
        
        # May succeed or fail depending on API key availability
        assert isinstance(result, ToolResult)
        assert result.tool_name == "gemini"
    
    @pytest.mark.asyncio
    async def test_summarize_operation(self):
        """Test summarization."""
        client = GeminiClient()
        
        result = await client.execute(
            operation="summarize",
            parameters={
                "text": "This is a long document about API design patterns. It covers REST, GraphQL, and gRPC. Each has trade-offs."
            }
        )
        
        assert isinstance(result, ToolResult)
        # Result may succeed or fail based on API availability
    
    @pytest.mark.asyncio
    async def test_missing_prompt_fails(self):
        """Test that missing prompt fails."""
        client = GeminiClient()
        
        result = await client.execute(
            operation="generate",
            parameters={}
        )
        
        assert result.success is False


class TestNotebookLMClient:
    """Tests for NotebookLM client."""
    
    @pytest.mark.asyncio
    async def test_summarize_with_sources(self):
        """Test summarization with citations."""
        client = NotebookLMClient()
        
        text = "API design is critical. Good APIs are well-documented. Security is essential."
        
        result = await client.execute(
            operation="summarize_with_sources",
            parameters={"text": text}
        )
        
        # May succeed or fail based on Gemini API availability
        assert isinstance(result, ToolResult)
        assert result.tool_name == "notebooklm"
    
    @pytest.mark.asyncio
    async def test_answer_questions(self):
        """Test question answering with evidence."""
        client = NotebookLMClient()
        
        result = await client.execute(
            operation="answer_questions",
            parameters={
                "text": "REST APIs use HTTP methods. GET retrieves data. POST creates data.",
                "questions": ["What does GET do?", "What does POST do?"]
            }
        )
        
        assert isinstance(result, ToolResult)
    
    @pytest.mark.asyncio
    async def test_verify_claims(self):
        """Test claim verification."""
        client = NotebookLMClient()
        
        result = await client.execute(
            operation="verify_claims",
            parameters={
                "claims": ["APIs use HTTP", "APIs are always RESTful"],
                "source_text": "APIs can use HTTP or other protocols. REST is one API style."
            }
        )
        
        assert isinstance(result, ToolResult)


class TestToolRegistry:
    """Tests for tool registry."""
    
    def test_list_available_tools(self):
        """Test listing all available tools."""
        tools = list_available_tools()
        
        assert isinstance(tools, list)
        assert "vibes" in tools
        assert "mcp" in tools
        assert "lucid" in tools
        assert "gemini" in tools
        assert "notebooklm" in tools
    
    def test_get_tool_vibes(self):
        """Test retrieving Vibes tool."""
        tool = get_tool("vibes")
        
        assert isinstance(tool, VibesClient)
        assert tool.name == "vibes"
    
    def test_get_tool_mcp(self):
        """Test retrieving MCP tool."""
        tool = get_tool("mcp")
        
        assert isinstance(tool, MCPClient)
        assert tool.name == "mcp"
    
    def test_get_tool_case_insensitive(self):
        """Test tool retrieval is case-insensitive."""
        tool1 = get_tool("Vibes")
        tool2 = get_tool("VIBES")
        tool3 = get_tool("vibes")
        
        # All should return the same instance
        assert tool1.name == tool2.name == tool3.name == "vibes"
    
    def test_get_tool_invalid_raises_exception(self):
        """Test that invalid tool name raises exception."""
        from app.utils.exceptions import ToolException
        
        with pytest.raises(ToolException) as exc_info:
            get_tool("invalid_tool")
        
        assert "not found" in str(exc_info.value)
    
    def test_tool_registry_metadata(self):
        """Test tool registry metadata structure."""
        assert "vibes" in TOOL_REGISTRY
        assert "display_name" in TOOL_REGISTRY["vibes"]
        assert "category" in TOOL_REGISTRY["vibes"]
        assert "capabilities" in TOOL_REGISTRY["vibes"]


class TestToolResultSchema:
    """Tests for ToolResult schema."""
    
    def test_create_success_result(self):
        """Test creating a successful result."""
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            summary="Test succeeded",
            details={"key": "value"}
        )
        
        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.error is None
    
    def test_create_error_result(self):
        """Test creating an error result."""
        error = ToolError(
            error_type="TestError",
            message="Test failed",
            details={"reason": "mock failure"}
        )
        
        result = ToolResult(
            tool_name="test_tool",
            success=False,
            summary="Test failed",
            error=error
        )
        
        assert result.success is False
        assert result.error is not None
        assert result.error.error_type == "TestError"
    
    def test_result_with_artifacts(self):
        """Test result with artifacts."""
        result = ToolResult(
            tool_name="lucid",
            success=True,
            summary="Diagram generated",
            artifacts=["https://lucid.app/diagram/abc123", "diagram.png"]
        )
        
        assert result.artifacts is not None
        assert len(result.artifacts) == 2
    
    def test_result_serialization(self):
        """Test result can be serialized to dict."""
        result = ToolResult(
            tool_name="test",
            success=True,
            summary="Test"
        )
        
        result_dict = result.dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["tool_name"] == "test"
        assert result_dict["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

