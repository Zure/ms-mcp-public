"""Portfolio MCP Server - Main Application.

This is a Model Context Protocol (MCP) server for managing investment portfolios,
holdings, and watchlists. It demonstrates stateful operations, data persistence,
and authenticated access to portfolio management tools.

Features:
- API key-based authentication
- Portfolio holdings management (CRUD operations)
- Watchlist management
- Transaction history tracking
- Resource exposure for cross-server composition
"""

import logging
import sys
from typing import Optional
from fastmcp import FastMCP

# Import configuration
from config.settings import settings
from config.auth import AuthLogger, AuthenticationMiddleware

# Import database components
from database.factory import DatabaseFactory
from services.portfolio_service import PortfolioService

# Import tools
from tools import register_tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global service instance
_portfolio_service: Optional[PortfolioService] = None
_db_factory: Optional[DatabaseFactory] = None


async def get_portfolio_service() -> PortfolioService:
    """Get or create the portfolio service instance.
    
    Initializes database connection, verifies/creates containers,
    and sets up all repositories on first call.
    
    Returns:
        PortfolioService: The singleton portfolio service instance
    """
    global _portfolio_service, _db_factory
    
    if _portfolio_service is None:
        logger.info("🔧 Initializing Portfolio Service...")
        
        # Initialize database factory
        _db_factory = DatabaseFactory(database_mode=settings.database_mode)
        
        # Create and configure client
        _db_factory.create_client(
            cosmos_endpoint=settings.cosmos_endpoint,
            cosmos_key=settings.cosmos_key,
            cosmos_database_name=settings.cosmos_database_name
        )
        
        # Initialize all repositories (this will check/create containers)
        await _db_factory.initialize_all()
        
        # Create repositories
        holdings_repo = _db_factory.create_holdings_repository()
        transactions_repo = _db_factory.create_transactions_repository()
        portfolio_repo = _db_factory.create_portfolio_repository()
        
        # Create service
        _portfolio_service = PortfolioService(holdings_repo, transactions_repo, portfolio_repo)
        logger.info("✅ Portfolio service initialized successfully")
    
    return _portfolio_service


# Initialize FastMCP server with authentication
def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance.
    
    Returns:
        FastMCP: Configured server instance with authentication middleware
    """
    
    # Create FastMCP server
    mcp = FastMCP(name="MSLab/Portfolio")
    
    # Add authentication middleware
    auth_middleware = AuthenticationMiddleware(
        api_key=settings.api_key,
        dev_mode=settings.dev_mode,
        auth_enabled=settings.should_authenticate
    )
    mcp.add_middleware(auth_middleware)
    
    if settings.should_authenticate:
        logger.info("🔒 API key authentication middleware enabled")
    else:
        logger.warning("⚠️  Running in development mode - authentication bypassed")
        AuthLogger.log_auth_bypass("Development mode enabled")
    
    return mcp


# Create the server instance
mcp = create_server()

# Register all tools
register_tools(mcp, get_portfolio_service)

def main():
    """Main entry point for the server."""
    logger.info("=" * 60)
    logger.info(f"Starting {settings.server_name}")
    logger.info("=" * 60)
    logger.info(f"Configuration: {settings}")
    logger.info("=" * 60)
    
    if settings.should_authenticate:
        logger.info("🔐 Authentication: ENABLED")
        logger.info("   - API Key: ***" + settings.api_key[-4:] if settings.api_key else "")
        logger.info("   - Authorization header required: 'Authorization: Bearer <api-key>'")
    else:
        logger.warning("⚠️  Authentication: DISABLED (Development Mode)")
        logger.warning("   - This should NEVER be used in production!")
    
    logger.info("=" * 60)
    logger.info(f"Server ready at: http://{settings.server_host}:{settings.server_port}")
    logger.info("=" * 60)
    
    # Return the HTTP app for deployment
    return mcp


if __name__ == "__main__":
    # For running with: uvicorn server:app --reload
   main().run(transport="http", host="127.0.0.1", port=8000)
