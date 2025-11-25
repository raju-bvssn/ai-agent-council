"""
Lucid AI client for diagram generation.

Provides:
- Architecture diagram generation
- Sequence diagram generation
- Data flow diagram generation
- Integration flow visualization

For prototype/demo mode, uses Gemini to generate Mermaid diagram
code as a fallback when Lucid API is unavailable.
"""

import os
from typing import Any, Dict, Optional

from app.tools.base_tool import BaseTool, with_timeout, with_retry
from app.tools.schemas import ToolResult
from app.llm.providers import get_gemini_provider


class LucidClient(BaseTool):
    """
    Client for Lucid AI diagram generation.
    
    Generates visual diagrams for architecture, sequences, data flows,
    and integration patterns.
    """
    
    @property
    def name(self) -> str:
        return "lucid"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Lucid client.
        
        Args:
            config: Optional configuration including API keys and endpoints
        """
        super().__init__(config)
        self.api_key = self.config.get("api_key") or os.getenv("LUCID_API_KEY")
        self.endpoint = self.config.get("endpoint") or os.getenv("LUCID_ENDPOINT")
        self.use_mock = not self.api_key  # Use Mermaid fallback if no API key
        
        if self.use_mock:
            self.logger.warning("lucid_mock_mode", reason="No API key found, using Mermaid fallback")
    
    @with_timeout(seconds=60)
    @with_retry(max_attempts=2)
    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute Lucid operation.
        
        Operations:
        - generate_architecture: Create architecture diagram
        - generate_sequence: Create sequence diagram
        - generate_dataflow: Create data flow diagram
        - generate_integration_flow: Create integration flow diagram
        """
        if operation == "generate_architecture":
            return await self._generate_architecture(parameters.get("description"))
        elif operation == "generate_sequence":
            return await self._generate_sequence(parameters.get("flows"))
        elif operation == "generate_dataflow":
            return await self._generate_dataflow(parameters.get("description"))
        elif operation == "generate_integration_flow":
            return await self._generate_integration_flow(parameters.get("description"))
        else:
            return self._create_error_result(
                f"Unknown operation: {operation}",
                error_type="InvalidOperation"
            )
    
    async def _generate_architecture(self, description: Optional[str]) -> ToolResult:
        """
        Generate an architecture diagram.
        
        Args:
            description: Architecture description
            
        Returns:
            ToolResult with diagram (Mermaid code or Lucid URL)
        """
        if not description:
            return self._create_error_result(
                "No description provided",
                error_type="InvalidParameter"
            )
        
        if self.use_mock:
            return await self._generate_mermaid_architecture(description)
        
        # TODO: Implement actual Lucid API call
        return await self._generate_mermaid_architecture(description)
    
    async def _generate_mermaid_architecture(self, description: str) -> ToolResult:
        """
        Use Gemini to generate Mermaid architecture diagram code.
        
        Args:
            description: Architecture description
            
        Returns:
            ToolResult with Mermaid diagram code
        """
        provider = get_gemini_provider()
        
        prompt = f"""
You are a Mermaid diagram expert. Generate a clean, professional architecture diagram for this system:

{description}

Requirements:
1. Use Mermaid flowchart syntax (graph TD or LR)
2. Include key components and their relationships
3. Use meaningful component names
4. Show data flow with labeled arrows
5. Group related components with subgraphs if applicable
6. Use appropriate shapes (rectangles for services, cylinders for databases, etc.)

Return ONLY a JSON object:
{{
  "mermaid_code": "<valid mermaid flowchart code>",
  "description": "<brief explanation of the diagram>",
  "key_components": ["<component1>", "<component2>"]
}}
"""
        
        try:
            response = await provider.generate_with_safety(
                prompt,
                model="gemini-1.5-flash",
                json_mode=True
            )
            
            mermaid_code = response.get("mermaid_code", "")
            
            return self._create_success_result(
                summary="Architecture diagram generated",
                details={
                    "diagram_type": "architecture",
                    "format": "mermaid",
                    "mermaid_code": mermaid_code,
                    "description": response.get("description", ""),
                    "key_components": response.get("key_components", [])
                },
                artifacts=[f"mermaid:{mermaid_code}"],
                metadata={"diagram_engine": "gemini-mermaid-fallback"}
            )
            
        except Exception as e:
            self.logger.error("lucid_architecture_generation_failed", error=str(e))
            return self._create_error_result(
                f"Diagram generation failed: {str(e)}",
                error_type="GenerationError"
            )
    
    async def _generate_sequence(self, flows: Optional[str]) -> ToolResult:
        """
        Generate a sequence diagram.
        
        Args:
            flows: Description of interaction flows
            
        Returns:
            ToolResult with sequence diagram
        """
        if not flows:
            return self._create_error_result(
                "No flows provided",
                error_type="InvalidParameter"
            )
        
        if self.use_mock:
            return await self._generate_mermaid_sequence(flows)
        
        # TODO: Implement actual Lucid API call
        return await self._generate_mermaid_sequence(flows)
    
    async def _generate_mermaid_sequence(self, flows: str) -> ToolResult:
        """
        Use Gemini to generate Mermaid sequence diagram code.
        
        Args:
            flows: Flow description
            
        Returns:
            ToolResult with Mermaid sequence diagram code
        """
        provider = get_gemini_provider()
        
        prompt = f"""
You are a Mermaid diagram expert. Generate a sequence diagram for these interactions:

{flows}

Requirements:
1. Use Mermaid sequenceDiagram syntax
2. Show clear actor/participant interactions
3. Include request/response messages
4. Add notes for important steps
5. Show alt/opt blocks for conditional flows if applicable

Return ONLY a JSON object:
{{
  "mermaid_code": "<valid mermaid sequence diagram code>",
  "description": "<brief explanation>",
  "participants": ["<actor1>", "<actor2>"]
}}
"""
        
        try:
            response = await provider.generate_with_safety(
                prompt,
                model="gemini-1.5-flash",
                json_mode=True
            )
            
            mermaid_code = response.get("mermaid_code", "")
            
            return self._create_success_result(
                summary="Sequence diagram generated",
                details={
                    "diagram_type": "sequence",
                    "format": "mermaid",
                    "mermaid_code": mermaid_code,
                    "description": response.get("description", ""),
                    "participants": response.get("participants", [])
                },
                artifacts=[f"mermaid:{mermaid_code}"],
                metadata={"diagram_engine": "gemini-mermaid-fallback"}
            )
            
        except Exception as e:
            self.logger.error("lucid_sequence_generation_failed", error=str(e))
            return self._create_error_result(
                f"Sequence diagram generation failed: {str(e)}",
                error_type="GenerationError"
            )
    
    async def _generate_dataflow(self, description: Optional[str]) -> ToolResult:
        """
        Generate a data flow diagram.
        
        Args:
            description: Data flow description
            
        Returns:
            ToolResult with data flow diagram
        """
        if not description:
            return self._create_error_result(
                "No description provided",
                error_type="InvalidParameter"
            )
        
        provider = get_gemini_provider()
        
        prompt = f"""
You are a Mermaid diagram expert. Generate a data flow diagram for this system:

{description}

Requirements:
1. Use Mermaid flowchart syntax
2. Show data sources, transformations, and destinations
3. Label data flows with data types/formats
4. Use appropriate shapes (cylinder for storage, rectangle for process)

Return ONLY a JSON object:
{{
  "mermaid_code": "<valid mermaid code>",
  "description": "<brief explanation>",
  "data_entities": ["<entity1>", "<entity2>"]
}}
"""
        
        try:
            response = await provider.generate_with_safety(
                prompt,
                model="gemini-1.5-flash",
                json_mode=True
            )
            
            mermaid_code = response.get("mermaid_code", "")
            
            return self._create_success_result(
                summary="Data flow diagram generated",
                details={
                    "diagram_type": "dataflow",
                    "format": "mermaid",
                    "mermaid_code": mermaid_code,
                    "description": response.get("description", ""),
                    "data_entities": response.get("data_entities", [])
                },
                artifacts=[f"mermaid:{mermaid_code}"],
                metadata={"diagram_engine": "gemini-mermaid-fallback"}
            )
            
        except Exception as e:
            self.logger.error("lucid_dataflow_generation_failed", error=str(e))
            return self._create_error_result(
                f"Data flow diagram generation failed: {str(e)}",
                error_type="GenerationError"
            )
    
    async def _generate_integration_flow(self, description: Optional[str]) -> ToolResult:
        """
        Generate an integration flow diagram.
        
        Args:
            description: Integration flow description
            
        Returns:
            ToolResult with integration flow diagram
        """
        if not description:
            return self._create_error_result(
                "No description provided",
                error_type="InvalidParameter"
            )
        
        provider = get_gemini_provider()
        
        prompt = f"""
You are a MuleSoft integration expert. Generate a Mermaid diagram for this integration flow:

{description}

Requirements:
1. Show source systems, Mule apps, and target systems
2. Include transformation steps
3. Show error handling paths
4. Label message flows with protocols/formats
5. Use clear, professional component names

Return ONLY a JSON object:
{{
  "mermaid_code": "<valid mermaid flowchart code>",
  "description": "<brief explanation>",
  "integration_points": ["<system1>", "<system2>"]
}}
"""
        
        try:
            response = await provider.generate_with_safety(
                prompt,
                model="gemini-1.5-flash",
                json_mode=True
            )
            
            mermaid_code = response.get("mermaid_code", "")
            
            return self._create_success_result(
                summary="Integration flow diagram generated",
                details={
                    "diagram_type": "integration_flow",
                    "format": "mermaid",
                    "mermaid_code": mermaid_code,
                    "description": response.get("description", ""),
                    "integration_points": response.get("integration_points", [])
                },
                artifacts=[f"mermaid:{mermaid_code}"],
                metadata={"diagram_engine": "gemini-mermaid-fallback"}
            )
            
        except Exception as e:
            self.logger.error("lucid_integration_flow_generation_failed", error=str(e))
            return self._create_error_result(
                f"Integration flow diagram generation failed: {str(e)}",
                error_type="GenerationError"
            )

