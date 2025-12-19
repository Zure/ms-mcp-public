"""Database factory for creating database clients and repositories.

This module provides a factory pattern for creating database clients
and repositories, allowing easy switching between different database
providers (Cosmos DB, file-based storage, etc.).
"""

import logging
from typing import Optional
from database.client import IPortfolioDatabaseClient, CosmosDBClient
from database.repository import (
    CosmosHoldingsRepository,
    CosmosTransactionsRepository,
    CosmosWatchlistsRepository,
    CosmosPortfolioRepository
)

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """Factory for creating database clients and repositories."""
    
    def __init__(self, database_mode: str):
        """Initialize the database factory.
        
        Args:
            database_mode: Database mode ("cosmos" or "file")
        """
        self.database_mode = database_mode
        self._client: Optional[IPortfolioDatabaseClient] = None
        self._holdings_repo = None
        self._transactions_repo = None
        self._watchlists_repo = None
        self._portfolio_repo = None
    
    def create_client(
        self,
        cosmos_endpoint: Optional[str] = None,
        cosmos_key: Optional[str] = None,
        cosmos_database_name: str = "portfolio-mcp"
    ) -> IPortfolioDatabaseClient:
        """Create and return a database client.
        
        Args:
            cosmos_endpoint: Cosmos DB endpoint (required for cosmos mode)
            cosmos_key: Cosmos DB key (required for cosmos mode)
            cosmos_database_name: Cosmos DB database name
            
        Returns:
            Database client instance
            
        Raises:
            ValueError: If required parameters are missing
        """
        if self.database_mode == "cosmos":
            if not cosmos_endpoint or not cosmos_key:
                raise ValueError(
                    "cosmos_endpoint and cosmos_key are required for Cosmos DB mode"
                )
            
            self._client = CosmosDBClient(
                endpoint=cosmos_endpoint,
                key=cosmos_key,
                database_name=cosmos_database_name
            )
            logger.info("Created Cosmos DB client")
            
        else:
            raise ValueError(f"Unsupported database mode: {self.database_mode}")
        
        return self._client
    
    def get_client(self) -> Optional[IPortfolioDatabaseClient]:
        """Get the current database client.
        
        Returns:
            Database client instance or None if not created
        """
        return self._client
    
    def create_holdings_repository(self):
        """Create and return a holdings repository.
        
        Returns:
            Holdings repository instance
            
        Raises:
            RuntimeError: If client is not initialized
        """
        if not self._client:
            raise RuntimeError("Database client not initialized. Call create_client() first.")
        
        if self.database_mode == "cosmos":
            if self._holdings_repo is None:
                container = self._client.get_container("holdings")
                self._holdings_repo = CosmosHoldingsRepository(container)
                logger.info("Created Cosmos DB holdings repository")
        
        return self._holdings_repo
    
    def create_transactions_repository(self):
        """Create and return a transactions repository.
        
        Returns:
            Transactions repository instance
            
        Raises:
            RuntimeError: If client is not initialized
        """
        if not self._client:
            raise RuntimeError("Database client not initialized. Call create_client() first.")
        
        if self.database_mode == "cosmos":
            if self._transactions_repo is None:
                container = self._client.get_container("transactions")
                self._transactions_repo = CosmosTransactionsRepository(container)
                logger.info("Created Cosmos DB transactions repository")
        
        return self._transactions_repo
    
    def create_watchlists_repository(self):
        """Create and return a watchlists repository.
        
        Returns:
            Watchlists repository instance
            
        Raises:
            RuntimeError: If client is not initialized
        """
        if not self._client:
            raise RuntimeError("Database client not initialized. Call create_client() first.")
        
        if self.database_mode == "cosmos":
            if self._watchlists_repo is None:
                container = self._client.get_container("watchlists")
                self._watchlists_repo = CosmosWatchlistsRepository(container)
                logger.info("Created Cosmos DB watchlists repository")
        
        return self._watchlists_repo
    
    def create_portfolio_repository(self):
        """Create and return a portfolio repository.
        
        Returns:
            Portfolio repository instance
            
        Raises:
            RuntimeError: If client is not initialized
        """
        if not self._client:
            raise RuntimeError("Database client not initialized. Call create_client() first.")
        
        if self.database_mode == "cosmos":
            if self._portfolio_repo is None:
                container = self._client.get_container("portfolios")
                self._portfolio_repo = CosmosPortfolioRepository(container)
                logger.info("Created Cosmos DB portfolio repository")
        
        return self._portfolio_repo
    
    async def initialize_all(self) -> None:
        """Initialize database connection and all repositories.
        
        This is a convenience method that:
        1. Connects to the database
        2. Initializes the database schema
        3. Creates all repositories
        
        Raises:
            RuntimeError: If client is not initialized
        """
        if not self._client:
            raise RuntimeError("Database client not initialized. Call create_client() first.")
        
        logger.info("Initializing database...")
        
        # Connect to database
        await self._client.connect()
        
        # Initialize schema
        await self._client.initialize_database()
        
        # Create all repositories
        self.create_holdings_repository()
        self.create_transactions_repository()
        self.create_watchlists_repository()
        self.create_portfolio_repository()
        
        logger.info("✅ Database fully initialized")
    
    async def health_check(self) -> bool:
        """Check database health.
        
        Returns:
            True if database is healthy, False otherwise
        """
        if not self._client:
            return False
        
        return await self._client.health_check()
    
    async def shutdown(self) -> None:
        """Shutdown database connections gracefully."""
        if self._client:
            logger.info("Shutting down database connections...")
            await self._client.disconnect()
            self._client = None
            self._holdings_repo = None
            self._transactions_repo = None
            self._watchlists_repo = None
            self._portfolio_repo = None
            logger.info("✅ Database connections closed")


# Global factory instance (will be initialized in server.py)
_factory: Optional[DatabaseFactory] = None


def get_database_factory() -> DatabaseFactory:
    """Get the global database factory instance.
    
    Returns:
        DatabaseFactory instance
        
    Raises:
        RuntimeError: If factory is not initialized
    """
    if _factory is None:
        raise RuntimeError(
            "Database factory not initialized. Call initialize_database_factory() first."
        )
    return _factory


def initialize_database_factory(database_mode: str) -> DatabaseFactory:
    """Initialize the global database factory.
    
    Args:
        database_mode: Database mode ("cosmos" or "file")
        
    Returns:
        Initialized DatabaseFactory instance
    """
    global _factory
    _factory = DatabaseFactory(database_mode)
    logger.info(f"Initialized database factory with mode: {database_mode}")
    return _factory
