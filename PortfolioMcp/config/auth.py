"""Authentication utilities for Portfolio MCP Server.

This module provides authentication helpers, logging, and error handling
for API key-based authentication in the FastMCP server.
"""

import logging
from datetime import datetime
from typing import Optional, Any
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.exceptions import McpError
import mcp.types as mt

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthLogger:
    """Handles logging of authentication events."""
    
    @staticmethod
    def log_auth_success(client_info: Optional[str] = None):
        """Log successful authentication attempt.
        
        Args:
            client_info: Optional information about the client (e.g., client_id)
        """
        timestamp = datetime.utcnow().isoformat()
        logger.info(
            f"Authentication successful - "
            f"timestamp={timestamp}, "
            f"client={client_info or 'unknown'}"
        )
    
    @staticmethod
    def log_auth_failure(reason: str, client_info: Optional[str] = None):
        """Log failed authentication attempt.
        
        Args:
            reason: Reason for authentication failure
            client_info: Optional information about the client
        """
        timestamp = datetime.utcnow().isoformat()
        logger.warning(
            f"Authentication failed - "
            f"timestamp={timestamp}, "
            f"reason={reason}, "
            f"client={client_info or 'unknown'}"
        )
    
    @staticmethod
    def log_auth_bypass(reason: str):
        """Log authentication bypass (e.g., dev mode).
        
        Args:
            reason: Reason for authentication bypass
        """
        logger.debug(f"Authentication bypassed - reason={reason}")


def get_authenticated_user() -> Optional[dict]:
    """Get information about the currently authenticated user.
    
    This function retrieves authentication information from the FastMCP
    access token, if available. It can be used in tools to access
    authentication context.
    
    Returns:
        dict: Dictionary containing authentication information, or None if not authenticated.
        Example:
        {
            "authenticated": True,
            "client_id": "client-123",
            "scopes": ["read", "write"],
            "expires_at": "2024-12-12T10:30:00Z"
        }
    """
    token: Optional[AccessToken] = get_access_token()
    
    if token is None:
        return {
            "authenticated": False,
            "client_id": None,
            "scopes": [],
            "expires_at": None
        }
    
    return {
        "authenticated": True,
        "client_id": token.client_id,
        "scopes": token.scopes if hasattr(token, 'scopes') else [],
        "expires_at": token.expires_at if hasattr(token, 'expires_at') else None,
        "claims": token.claims if hasattr(token, 'claims') else {}
    }


class AuthenticationMiddleware(Middleware):
    """FastMCP middleware that validates API key authentication for tool calls.
    
    This middleware intercepts tool call requests and validates the API key
    from the context metadata. It can be bypassed in development mode.
    """
    
    def __init__(self, api_key: str, dev_mode: bool = False, auth_enabled: bool = True):
        """Initialize the authentication middleware.
        
        Args:
            api_key: The valid API key to check against
            dev_mode: Whether to bypass authentication (for development)
            auth_enabled: Whether authentication is globally enabled
        """
        self.api_key = api_key
        self.dev_mode = dev_mode
        self.auth_enabled = auth_enabled
    
    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, list[mt.TextContent | mt.ImageContent | mt.EmbeddedResource]]
    ) -> list[mt.TextContent | mt.ImageContent | mt.EmbeddedResource]:
        """Validate authentication before calling a tool.
        
        Args:
            context: The middleware context containing the request
            call_next: The next handler in the chain
            
        Returns:
            The result from the tool call
            
        Raises:
            MCPError: If authentication fails
        """
        # Skip auth in dev mode
        if self.dev_mode:
            AuthLogger.log_auth_bypass("Development mode enabled")
            return await call_next(context)
        
        # Skip auth if disabled
        if not self.auth_enabled:
            return await call_next(context)
        
        # Extract metadata from context
        metadata = getattr(context, 'metadata', {}) or {}
        auth_header = metadata.get('authorization') or metadata.get('Authorization')
        
        if not auth_header:
            AuthLogger.log_auth_failure("Missing authorization in metadata", "unknown")
            raise McpError(
                -32001,
                "Missing authentication. Please provide API key in metadata['authorization'] as 'Bearer <api-key>'"
            )
        
        # Parse Bearer token
        if isinstance(auth_header, str):
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                AuthLogger.log_auth_failure("Invalid authorization format", "unknown")
                raise McpError(
                    -32002,
                    "Invalid authorization format. Expected 'Bearer <api-key>'"
                )
            token = parts[1]
        else:
            token = str(auth_header)
        
        # Validate token
        if token != self.api_key:
            AuthLogger.log_auth_failure("Invalid API key", "unknown")
            raise McpError(
                -32003,
                "Invalid API key"
            )
        
        # Authentication successful
        AuthLogger.log_auth_success("authenticated")
        
        # Continue to the actual tool call
        return await call_next(context)


def require_authentication():
    """Decorator/dependency to require authentication for a tool.
    
    This function can be used as a dependency in FastMCP tools to
    ensure that only authenticated users can access them.
    
    Raises:
        AuthenticationError: If user is not authenticated
    """
    user = get_authenticated_user()
    if not user["authenticated"]:
        AuthLogger.log_auth_failure("No authentication provided")
        raise AuthenticationError(
            "Authentication required. "
            "Please provide a valid API key in the Authorization header."
        )
    
    AuthLogger.log_auth_success(user.get("client_id"))
    return user


def create_auth_error_response(message: str, status_code: int = 401) -> dict:
    """Create a standardized authentication error response.
    
    Args:
        message: Error message to include
        status_code: HTTP status code (default: 401 Unauthorized)
    
    Returns:
        dict: Error response dictionary
    """
    return {
        "error": "AuthenticationError",
        "message": message,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat()
    }
