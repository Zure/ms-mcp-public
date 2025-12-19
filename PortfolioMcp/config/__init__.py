"""Configuration package for Portfolio MCP Server."""

from .settings import settings
from .auth import (
    AuthLogger,
    AuthenticationError,
    get_authenticated_user,
    require_authentication,
    create_auth_error_response
)

__all__ = [
    "settings",
    "AuthLogger",
    "AuthenticationError",
    "get_authenticated_user",
    "require_authentication",
    "create_auth_error_response"
]
