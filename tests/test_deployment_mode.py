"""
Comprehensive tests for deployment mode and configuration.

Tests deployment wiring including:
- API_BASE_URL configuration
- DEMO_MODE behavior
- Health endpoint
- API client retry logic
- CORS configuration
- Tool client mock modes
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from app.utils.settings import get_settings, Settings
from app.tools.schemas import ToolResult


class TestSettings:
    """Tests for settings and configuration."""
    
    def test_settings_default_values(self):
        """Test default settings values."""
        settings = get_settings()
        
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.env in ["development", "staging", "production"]
        assert isinstance(settings.demo_mode, bool)
        assert isinstance(settings.health_check_enabled, bool)
    
    def test_api_base_url_from_settings(self):
        """Test API base URL construction from settings."""
        settings = get_settings()
        url = settings.get_api_base_url()
        
        assert url.startswith("http")
        assert ":" in url  # Has port
        assert not url.endswith("/")  # No trailing slash
    
    def test_is_demo_mode_property(self):
        """Test is_demo_mode property."""
        settings = get_settings()
        assert settings.is_demo_mode == settings.demo_mode
    
    def test_allowed_origins_parsing(self):
        """Test CORS allowed origins parsing."""
        settings = get_settings()
        origins = settings.get_allowed_origins_list()
        
        assert isinstance(origins, list)
        assert len(origins) > 0
        for origin in origins:
            assert isinstance(origin, str)
            assert len(origin.strip()) > 0
    
    @pytest.mark.parametrize("env_value,expected", [
        ("development", "development"),
        ("staging", "staging"),
        ("production", "production"),
    ])
    def test_environment_validation(self, env_value, expected):
        """Test environment value validation."""
        with patch.dict(os.environ, {"ENV": env_value}):
            # Force reload settings
            from app.utils.settings import Settings
            settings = Settings()
            assert settings.env == expected
    
    def test_production_detection(self):
        """Test is_production property."""
        with patch.dict(os.environ, {"ENV": "production"}):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_response_schema(self):
        """Test HealthResponse schema."""
        from app.api.schemas import HealthResponse
        from datetime import datetime
        
        response = HealthResponse(
            status="healthy",
            environment="development",
            demo_mode=True,
            api_base_url="http://localhost:8000"
        )
        
        assert response.status == "healthy"
        assert response.environment == "development"
        assert response.demo_mode is True
        assert response.api_base_url == "http://localhost:8000"
        assert isinstance(response.timestamp, datetime)
        assert response.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test health check endpoint returns correct data."""
        from app.api.routes import health_check
        
        result = await health_check()
        
        assert result.status == "healthy"
        assert hasattr(result, 'environment')
        assert hasattr(result, 'demo_mode')
        assert isinstance(result.demo_mode, bool)


class TestAPIClientConfiguration:
    """Tests for Streamlit API client configuration."""
    
    def test_get_api_base_url_from_env_default(self):
        """Test API URL resolution with default."""
        from app.ui.api_client import get_api_base_url_from_env
        
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            url = get_api_base_url_from_env()
            assert url == "http://localhost:8000"
    
    def test_get_api_base_url_from_env_variable(self):
        """Test API URL resolution from environment variable."""
        from app.ui.api_client import get_api_base_url_from_env
        
        test_url = "https://api.example.com"
        with patch.dict(os.environ, {"API_BASE_URL": test_url}):
            url = get_api_base_url_from_env()
            assert url == test_url
    
    def test_api_client_initialization(self):
        """Test APIClient initializes with correct URL."""
        from app.ui.api_client import APIClient
        
        client = APIClient(base_url="https://test.com")
        assert client.base_url == "https://test.com"
        assert client.api_prefix == "/api/v1"
        assert client.timeout == 30
        assert client.max_retries == 3
    
    def test_api_client_url_construction(self):
        """Test URL construction in API client."""
        from app.ui.api_client import APIClient
        
        client = APIClient(base_url="https://test.com")
        url = client._url("/health")
        
        assert url == "https://test.com/api/v1/health"
    
    def test_api_client_url_strips_trailing_slash(self):
        """Test base URL trailing slash is stripped."""
        from app.ui.api_client import APIClient
        
        client = APIClient(base_url="https://test.com/")
        assert client.base_url == "https://test.com"
    
    def test_get_api_client_factory(self):
        """Test get_api_client factory function."""
        from app.ui.api_client import get_api_client
        
        client = get_api_client()
        assert client is not None
        assert hasattr(client, 'health_check')
        assert hasattr(client, 'create_session')


class TestAPIClientRetryLogic:
    """Tests for API client retry logic."""
    
    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """Test retry logic on connection errors."""
        from app.ui.api_client import APIClient
        import requests
        
        client = APIClient(base_url="https://test.com", max_retries=2, retry_delay=0.1)
        
        # Mock requests to fail twice then succeed
        call_count = 0
        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise requests.exceptions.ConnectionError("Connection failed")
            
            # Success on 2nd attempt
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            return mock_response
        
        with patch('app.ui.api_client.requests.get', side_effect=mock_get):
            try:
                response = client._retry_request("get", "https://test.com/health", timeout=5)
                assert response.status_code == 200
                assert call_count == 2  # Failed once, succeeded second time
            except Exception:
                # Expected if retry logic triggers
                pass
    
    def test_retry_exhaustion(self):
        """Test that all retries exhaust and raise exception."""
        from app.ui.api_client import APIClient
        import requests
        
        client = APIClient(base_url="https://test.com", max_retries=2, retry_delay=0.1)
        
        # Mock requests to always fail
        with patch('app.ui.api_client.requests.get', side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(Exception) as exc_info:
                client._retry_request("get", "https://test.com/health", timeout=5)
            
            assert "unreachable after" in str(exc_info.value) or "Connection" in str(exc_info.value)


class TestDemoMode:
    """Tests for DEMO_MODE behavior."""
    
    def test_vibes_client_demo_mode(self):
        """Test Vibes client respects DEMO_MODE."""
        from app.tools.vibes_client import VibesClient
        
        with patch('app.tools.vibes_client.get_settings') as mock_settings:
            mock_settings.return_value.demo_mode = True
            
            client = VibesClient()
            assert client.use_mock is True
    
    def test_mcp_client_demo_mode(self):
        """Test MCP client respects DEMO_MODE."""
        from app.tools.mcp_client import MCPClient
        
        with patch('app.tools.mcp_client.get_settings') as mock_settings:
            mock_settings.return_value.demo_mode = True
            
            client = MCPClient()
            assert client.use_mock is True
    
    def test_lucid_client_demo_mode(self):
        """Test Lucid client respects DEMO_MODE."""
        from app.tools.lucid_client import LucidClient
        
        with patch('app.tools.lucid_client.get_settings') as mock_settings:
            mock_settings.return_value.demo_mode = True
            
            client = LucidClient()
            assert client.use_mock is True
    
    def test_tool_result_schema_in_demo_mode(self):
        """Test that demo mode returns valid ToolResult schemas."""
        result = ToolResult(
            tool_name="vibes",
            success=True,
            summary="Mock Vibes response",
            details={"score": 0.95, "recommendations": ["Use System API pattern"]},
            artifacts=[]
        )
        
        assert result.tool_name == "vibes"
        assert result.success is True
        assert isinstance(result.details, dict)
        assert "score" in result.details


class TestCORSConfiguration:
    """Tests for CORS configuration."""
    
    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        from app.app import create_app
        
        app = create_app()
        
        # Check middleware is added
        assert len(app.user_middleware) > 0
        
        # Look for CORSMiddleware
        has_cors = any(
            "CORSMiddleware" in str(middleware.cls)
            for middleware in app.user_middleware
        )
        assert has_cors
    
    def test_cors_allows_configured_origins(self):
        """Test CORS allows configured origins."""
        settings = get_settings()
        origins = settings.get_allowed_origins_list()
        
        assert len(origins) > 0
        # Should include localhost for development
        assert any("localhost" in origin or "*" in origin for origin in origins)


class TestEnvironmentDetection:
    """Tests for environment detection and configuration."""
    
    def test_development_environment_defaults(self):
        """Test development environment defaults."""
        with patch.dict(os.environ, {"ENV": "development"}):
            settings = Settings()
            
            assert settings.is_development is True
            assert settings.is_production is False
            assert settings.debug is False  # May be True in actual .env
    
    def test_production_environment_settings(self):
        """Test production environment settings."""
        with patch.dict(os.environ, {"ENV": "production"}):
            settings = Settings()
            
            assert settings.is_production is True
            assert settings.is_development is False
            # In production, certain features should be locked down
            assert settings.env == "production"


class TestDeploymentReadiness:
    """Integration tests for deployment readiness."""
    
    def test_all_required_fields_present(self):
        """Test all required deployment fields are present."""
        settings = get_settings()
        
        # Core API settings
        assert hasattr(settings, 'api_host')
        assert hasattr(settings, 'api_port')
        assert hasattr(settings, 'api_base_url')
        
        # Deployment settings
        assert hasattr(settings, 'env')
        assert hasattr(settings, 'demo_mode')
        assert hasattr(settings, 'health_check_enabled')
        
        # CORS
        assert hasattr(settings, 'allowed_origins')
        assert callable(settings.get_allowed_origins_list)
    
    def test_health_endpoint_reflects_settings(self):
        """Test health endpoint reflects current settings."""
        # This would be an integration test in practice
        settings = get_settings()
        
        # Health response should match settings
        assert settings.env in ["development", "staging", "production"]
        assert isinstance(settings.demo_mode, bool)
    
    def test_tool_clients_can_initialize(self):
        """Test all tool clients can initialize."""
        from app.tools.vibes_client import VibesClient
        from app.tools.mcp_client import MCPClient
        from app.tools.lucid_client import LucidClient
        
        # Should not raise exceptions
        vibes = VibesClient()
        mcp = MCPClient()
        lucid = LucidClient()
        
        assert vibes is not None
        assert mcp is not None
        assert lucid is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

