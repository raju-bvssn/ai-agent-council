"""
Configuration loader for Agent Council system.

Provides utilities for loading and validating configuration files.
Supports JSON, YAML, and environment-based configuration.
"""

import json
from pathlib import Path
from typing import Any, Optional

from app.utils.exceptions import ConfigurationException
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """
    Configuration loader with validation and fallback support.

    Implements Single Responsibility Principle: only handles config loading.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or Path("config")
        self._cache: dict[str, Any] = {}

    def load_json(self, filename: str, required: bool = True) -> dict[str, Any]:
        """
        Load JSON configuration file.

        Args:
            filename: Name of the JSON file (without path)
            required: Whether the file is required to exist

        Returns:
            Parsed JSON content as dictionary

        Raises:
            ConfigurationException: If required file is missing or invalid
        """
        cache_key = f"json:{filename}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        file_path = self.config_dir / filename

        if not file_path.exists():
            if required:
                raise ConfigurationException(
                    f"Required configuration file not found: {file_path}",
                    details={"file_path": str(file_path)}
                )
            logger.warning("config_file_not_found", filename=filename, path=str(file_path))
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self._cache[cache_key] = config
            logger.info("config_loaded", filename=filename, path=str(file_path))
            return config
        except json.JSONDecodeError as e:
            raise ConfigurationException(
                f"Invalid JSON in configuration file: {filename}",
                details={"error": str(e), "file_path": str(file_path)}
            )
        except Exception as e:
            raise ConfigurationException(
                f"Failed to load configuration file: {filename}",
                details={"error": str(e), "file_path": str(file_path)}
            )

    def load_agent_config(self, agent_name: str) -> dict[str, Any]:
        """
        Load agent-specific configuration.

        Args:
            agent_name: Name of the agent (e.g., 'master', 'reviewer')

        Returns:
            Agent configuration dictionary
        """
        return self.load_json(f"agents/{agent_name}.json", required=False)

    def load_workflow_config(self) -> dict[str, Any]:
        """
        Load workflow configuration.

        Returns:
            Workflow configuration dictionary
        """
        return self.load_json("workflow.json", required=False)

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()
        logger.info("config_cache_cleared")


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """
    Get global ConfigLoader instance.

    Returns:
        ConfigLoader singleton
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

