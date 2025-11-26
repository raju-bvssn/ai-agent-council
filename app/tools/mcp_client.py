"""
MCP (MuleSoft Control Plane) Server client for platform metadata.

Provides access to:
- Environment configuration
- API Manager metadata
- Runtime Fabric / CloudHub deployment info
- Policies, VPCs, client apps, SLAs
- Monitoring and analytics data

For prototype/demo mode, returns structured mock data with realistic
platform configurations.
"""

import os
from typing import Any, Dict, List, Optional

from app.tools.base_tool import BaseTool, with_timeout, with_retry
from app.tools.schemas import ToolResult
from app.utils.settings import get_settings


class MCPClient(BaseTool):
    """
    Client for MuleSoft Control Plane (MCP) Server integration.
    
    Fetches platform metadata, environment configuration, and deployment
    information for informed architectural decisions.
    """
    
    @property
    def name(self) -> str:
        return "mcp"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MCP client.
        
        Args:
            config: Optional configuration including API endpoint and credentials
        """
        super().__init__(config)
        settings = get_settings()
        
        self.api_key = self.config.get("api_key") or os.getenv("MCP_API_KEY")
        self.org_id = self.config.get("org_id") or os.getenv("MCP_ORG_ID")
        self.endpoint = self.config.get("endpoint") or os.getenv("MCP_ENDPOINT", "https://anypoint.mulesoft.com")
        
        # Use mock mode if DEMO_MODE is enabled or no API key
        self.use_mock = settings.demo_mode or not self.api_key
        
        if self.use_mock:
            reason = "DEMO_MODE enabled" if settings.demo_mode else "No API key found"
            self.logger.warning("mcp_mock_mode", reason=f"{reason}, using mock data")
    
    @with_timeout(seconds=30)
    @with_retry(max_attempts=3)
    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute MCP operation.
        
        Operations:
        - get_environment_info: Fetch environment details
        - get_api_metadata: Get API Manager metadata
        - list_policies: List available/applied policies
        - get_runtime_info: Get Runtime Fabric or CloudHub info
        - get_deployment_config: Get deployment configuration
        - list_client_apps: List registered client applications
        """
        if operation == "get_environment_info":
            return await self._get_environment_info(parameters.get("env_id"))
        elif operation == "get_api_metadata":
            return await self._get_api_metadata(parameters.get("api_id"))
        elif operation == "list_policies":
            return await self._list_policies(parameters.get("env_id"))
        elif operation == "get_runtime_info":
            return await self._get_runtime_info(parameters.get("runtime_id"))
        elif operation == "get_deployment_config":
            return await self._get_deployment_config(parameters.get("deployment_id"))
        elif operation == "list_client_apps":
            return await self._list_client_apps(parameters.get("env_id"))
        else:
            return self._create_error_result(
                f"Unknown operation: {operation}",
                error_type="InvalidOperation"
            )
    
    async def _get_environment_info(self, env_id: Optional[str]) -> ToolResult:
        """
        Fetch environment configuration and metadata.
        
        Args:
            env_id: Environment identifier
            
        Returns:
            ToolResult with environment details
        """
        if not env_id and not self.use_mock:
            return self._create_error_result(
                "No env_id provided",
                error_type="InvalidParameter"
            )
        
        if self.use_mock:
            return self._mock_environment_info(env_id or "prod-env-001")
        
        # TODO: Implement actual MCP API call when credentials available
        return self._mock_environment_info(env_id)
    
    def _mock_environment_info(self, env_id: str) -> ToolResult:
        """Generate realistic mock environment data."""
        mock_data = {
            "environment_id": env_id,
            "name": "Production US-East",
            "type": "production",
            "is_production": True,
            "region": "us-east-1",
            "runtime_type": "CloudHub 2.0",
            "vpc_id": "vpc-12345abc",
            "vpn_enabled": True,
            "client_provider": "Active Directory",
            "monitoring": {
                "enabled": True,
                "log_level": "INFO",
                "retention_days": 30
            },
            "limits": {
                "max_workers": 10,
                "max_vcores": 4.0,
                "max_memory_mb": 16384
            },
            "deployed_apis": 47,
            "active_policies": 12
        }
        
        return self._create_success_result(
            summary=f"Environment: {mock_data['name']} ({mock_data['type']})",
            details=mock_data,
            metadata={"source": "mock", "env_id": env_id}
        )
    
    async def _get_api_metadata(self, api_id: Optional[str]) -> ToolResult:
        """
        Fetch API Manager metadata for a specific API.
        
        Args:
            api_id: API identifier
            
        Returns:
            ToolResult with API metadata
        """
        if not api_id and not self.use_mock:
            return self._create_error_result(
                "No api_id provided",
                error_type="InvalidParameter"
            )
        
        if self.use_mock:
            return self._mock_api_metadata(api_id or "customer-api-v1")
        
        # TODO: Implement actual API Manager call
        return self._mock_api_metadata(api_id)
    
    def _mock_api_metadata(self, api_id: str) -> ToolResult:
        """Generate realistic mock API metadata."""
        mock_data = {
            "api_id": api_id,
            "name": "Customer Management API",
            "version": "v1.2.3",
            "endpoint": "https://api.example.com/customers/v1",
            "asset_version": "1.2.3",
            "instance_label": "production",
            "status": "active",
            "autodiscovery_enabled": True,
            "applied_policies": [
                {"name": "Rate Limiting", "order": 1, "config": {"rate": "1000 req/hour"}},
                {"name": "Client ID Enforcement", "order": 2},
                {"name": "JWT Validation", "order": 3}
            ],
            "sla_tiers": [
                {"name": "Gold", "limits": "10000/hour", "approval": "automatic"},
                {"name": "Silver", "limits": "5000/hour", "approval": "automatic"}
            ],
            "consumers": 23,
            "avg_response_time_ms": 145,
            "requests_last_24h": 18763
        }
        
        return self._create_success_result(
            summary=f"API: {mock_data['name']} ({mock_data['status']})",
            details=mock_data,
            metadata={"source": "mock", "api_id": api_id}
        )
    
    async def _list_policies(self, env_id: Optional[str]) -> ToolResult:
        """
        List available policies in an environment.
        
        Args:
            env_id: Environment identifier
            
        Returns:
            ToolResult with policy list
        """
        if self.use_mock:
            return self._mock_policy_list(env_id or "prod-env-001")
        
        # TODO: Implement actual policy API call
        return self._mock_policy_list(env_id or "prod-env-001")
    
    def _mock_policy_list(self, env_id: str) -> ToolResult:
        """Generate realistic mock policy list."""
        policies = [
            {
                "id": "rate-limiting",
                "name": "Rate Limiting",
                "category": "Quality of Service",
                "description": "Throttles API requests based on SLA tiers"
            },
            {
                "id": "client-id-enforcement",
                "name": "Client ID Enforcement",
                "category": "Security",
                "description": "Validates client credentials"
            },
            {
                "id": "jwt-validation",
                "name": "JWT Validation",
                "category": "Security",
                "description": "Validates JSON Web Tokens"
            },
            {
                "id": "ip-whitelist",
                "name": "IP Whitelist",
                "category": "Security",
                "description": "Restricts access by IP address"
            },
            {
                "id": "cors",
                "name": "CORS",
                "category": "Compliance",
                "description": "Handles Cross-Origin Resource Sharing"
            },
            {
                "id": "spike-control",
                "name": "Spike Control",
                "category": "Quality of Service",
                "description": "Smooths traffic spikes"
            }
        ]
        
        return self._create_success_result(
            summary=f"Found {len(policies)} available policies",
            details={"policies": policies, "env_id": env_id},
            metadata={"source": "mock", "count": len(policies)}
        )
    
    async def _get_runtime_info(self, runtime_id: Optional[str]) -> ToolResult:
        """
        Fetch Runtime Fabric or CloudHub runtime information.
        
        Args:
            runtime_id: Runtime identifier
            
        Returns:
            ToolResult with runtime details
        """
        if self.use_mock:
            return self._mock_runtime_info(runtime_id or "rtf-prod-001")
        
        # TODO: Implement actual runtime API call
        return self._mock_runtime_info(runtime_id or "rtf-prod-001")
    
    def _mock_runtime_info(self, runtime_id: str) -> ToolResult:
        """Generate realistic mock runtime information."""
        mock_data = {
            "runtime_id": runtime_id,
            "name": "Production Runtime Fabric",
            "type": "Runtime Fabric",
            "version": "1.14.2",
            "status": "running",
            "region": "us-east-1",
            "nodes": [
                {"node_id": "node-1", "status": "healthy", "cpu_usage": 45, "memory_usage": 62},
                {"node_id": "node-2", "status": "healthy", "cpu_usage": 38, "memory_usage": 58},
                {"node_id": "node-3", "status": "healthy", "cpu_usage": 52, "memory_usage": 71}
            ],
            "deployed_apps": 23,
            "total_vcores": 12.0,
            "used_vcores": 8.5,
            "total_memory_gb": 48,
            "used_memory_gb": 31
        }
        
        return self._create_success_result(
            summary=f"Runtime: {mock_data['name']} ({mock_data['status']})",
            details=mock_data,
            metadata={"source": "mock", "runtime_id": runtime_id}
        )
    
    async def _get_deployment_config(self, deployment_id: Optional[str]) -> ToolResult:
        """
        Fetch deployment configuration.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            ToolResult with deployment configuration
        """
        if self.use_mock:
            return self._mock_deployment_config(deployment_id or "deploy-001")
        
        # TODO: Implement actual deployment API call
        return self._mock_deployment_config(deployment_id or "deploy-001")
    
    def _mock_deployment_config(self, deployment_id: str) -> ToolResult:
        """Generate realistic mock deployment configuration."""
        mock_data = {
            "deployment_id": deployment_id,
            "app_name": "customer-api",
            "version": "1.2.3",
            "runtime": "CloudHub 2.0",
            "replicas": 3,
            "vcore": 0.2,
            "region": "us-east-1",
            "properties": {
                "http.port": "8081",
                "anypoint.platform.client_id": "***",
                "db.host": "prod-db.example.com"
            },
            "logging_level": "INFO",
            "monitoring_enabled": True,
            "autoscaling": {
                "enabled": True,
                "min_replicas": 2,
                "max_replicas": 5,
                "target_cpu_percent": 70
            }
        }
        
        return self._create_success_result(
            summary=f"Deployment: {mock_data['app_name']} (v{mock_data['version']})",
            details=mock_data,
            metadata={"source": "mock", "deployment_id": deployment_id}
        )
    
    async def _list_client_apps(self, env_id: Optional[str]) -> ToolResult:
        """
        List registered client applications.
        
        Args:
            env_id: Environment identifier
            
        Returns:
            ToolResult with client application list
        """
        if self.use_mock:
            return self._mock_client_apps(env_id or "prod-env-001")
        
        # TODO: Implement actual client app API call
        return self._mock_client_apps(env_id or "prod-env-001")
    
    def _mock_client_apps(self, env_id: str) -> ToolResult:
        """Generate realistic mock client application list."""
        apps = [
            {
                "client_id": "a1b2c3d4e5f6",
                "name": "Mobile App v2",
                "owner": "mobile-team@example.com",
                "tier": "Gold",
                "status": "active",
                "api_contracts": 5
            },
            {
                "client_id": "f6e5d4c3b2a1",
                "name": "Web Portal",
                "owner": "web-team@example.com",
                "tier": "Silver",
                "status": "active",
                "api_contracts": 8
            },
            {
                "client_id": "1a2b3c4d5e6f",
                "name": "Partner Integration",
                "owner": "partner@external.com",
                "tier": "Gold",
                "status": "active",
                "api_contracts": 3
            }
        ]
        
        return self._create_success_result(
            summary=f"Found {len(apps)} registered client applications",
            details={"client_apps": apps, "env_id": env_id},
            metadata={"source": "mock", "count": len(apps)}
        )

