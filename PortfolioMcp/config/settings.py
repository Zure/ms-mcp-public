"""Configuration management for Portfolio MCP Server.

This module handles loading and validating environment variables,
including authentication settings and data storage paths.
"""

import os
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # Authentication settings
        self.api_key: Optional[str] = os.environ.get("MCP_API_KEY")
        self.auth_enabled: bool = os.environ.get("MCP_AUTH_ENABLED", "true").lower() == "true"
        
        # Development mode - bypasses authentication for local testing
        self.dev_mode: bool = os.environ.get("MCP_DEV_MODE", "false").lower() == "true"
        
        # Server settings
        self.server_name: str = os.environ.get("MCP_SERVER_NAME", "Portfolio MCP Server")
        self.server_host: str = os.environ.get("MCP_SERVER_HOST", "localhost")
        self.server_port: int = int(os.environ.get("MCP_SERVER_PORT", "8000"))
        
        # Data storage settings
        self.data_dir: Path = Path(os.environ.get("MCP_DATA_DIR", "./portfolio_data"))
        
        # Cosmos DB settings
        self.cosmos_endpoint: Optional[str] = os.environ.get("COSMOS_ENDPOINT")
        self.cosmos_key: Optional[str] = os.environ.get("COSMOS_KEY")
        self.cosmos_database_name: str = os.environ.get("COSMOS_DATABASE_NAME", "portfolio-mcp")
        
        # Database mode (cosmos or file)
        self.database_mode: str = os.environ.get("DATABASE_MODE", "cosmos").lower()
        
        # Logging settings
        self.log_level: str = os.environ.get("MCP_LOG_LEVEL", "INFO")
        self.log_auth_attempts: bool = os.environ.get("MCP_LOG_AUTH_ATTEMPTS", "true").lower() == "true"
        
        # Validate settings
        self._validate()
    
    def _validate(self):
        """Validate configuration settings."""
        if self.auth_enabled and not self.dev_mode and not self.api_key:
            raise ValueError(
                "MCP_API_KEY environment variable must be set when authentication is enabled. "
                "Set MCP_DEV_MODE=true to bypass authentication for local development."
            )
        
        if self.dev_mode:
            logger.warning(
                "⚠️  Development mode is enabled - authentication is bypassed! "
                "Do not use in production."
            )
        
        # Validate Cosmos DB configuration if using cosmos mode
        if self.database_mode == "cosmos":
            if not self.cosmos_endpoint:
                raise ValueError(
                    "COSMOS_ENDPOINT environment variable must be set when using Cosmos DB. "
                    "For local development, use the Cosmos DB emulator: "
                    "https://localhost:8081"
                )
            if not self.cosmos_key:
                raise ValueError(
                    "COSMOS_KEY environment variable must be set when using Cosmos DB. "
                    "For the emulator, use the default emulator key."
                )
    
    def __repr__(self) -> str:
        """Return string representation of settings (without sensitive data)."""
        return (
            f"Settings("
            f"server_name={self.server_name!r}, "
            f"auth_enabled={self.auth_enabled}, "
            f"dev_mode={self.dev_mode}, "
            f"api_key={'***' if self.api_key else None}, "
            f"database_mode={self.database_mode}, "
            f"cosmos_endpoint={self.cosmos_endpoint}, "
            f"data_dir={self.data_dir}"
            f")"
        )
    
    @property
    def should_authenticate(self) -> bool:
        """Determine if authentication should be enforced.
        
        Returns:
            bool: True if authentication should be enforced, False otherwise.
        """
        return self.auth_enabled and not self.dev_mode
    
    def __repr__(self) -> str:
        """Return string representation of settings (without sensitive data)."""
        return (
            f"Settings("
            f"server_name={self.server_name!r}, "
            f"auth_enabled={self.auth_enabled}, "
            f"dev_mode={self.dev_mode}, "
            f"api_key={'***' if self.api_key else None}, "
            f"data_dir={self.data_dir}"
            f")"
        )


# Global settings instance
settings = Settings()
