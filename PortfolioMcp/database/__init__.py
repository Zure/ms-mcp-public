"""Database package for Portfolio MCP Server."""

from .client import IPortfolioDatabaseClient, CosmosDBClient
from .repository import (
    IPortfolioRepository,
    CosmosHoldingsRepository,
    CosmosTransactionsRepository,
    CosmosWatchlistsRepository,
    CosmosPortfolioRepository
)
from .factory import DatabaseFactory, get_database_factory, initialize_database_factory

__all__ = [
    "IPortfolioDatabaseClient",
    "CosmosDBClient",
    "IPortfolioRepository",
    "CosmosHoldingsRepository",
    "CosmosTransactionsRepository",
    "CosmosWatchlistsRepository",
    "CosmosPortfolioRepository",
    "DatabaseFactory",
    "get_database_factory",
    "initialize_database_factory",
]
