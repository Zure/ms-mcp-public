"""Repository pattern implementation for portfolio data access.

This module provides an abstraction layer for data access operations,
using the repository pattern to decouple business logic from database specifics.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime
from azure.cosmos import ContainerProxy, exceptions

from models.domain import Holding, Transaction, Watchlist, Portfolio

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RepositoryException(Exception):
    """Base exception for repository operations."""
    pass


class ItemNotFoundException(RepositoryException):
    """Exception raised when an item is not found."""
    pass


class DuplicateItemException(RepositoryException):
    """Exception raised when trying to create an item that already exists."""
    pass


class IPortfolioRepository(ABC, Generic[T]):
    """Abstract interface for portfolio data repository.
    
    This generic interface defines standard CRUD operations for
    any data type in the portfolio system.
    """
    
    @abstractmethod
    async def get_by_id(self, item_id: str, partition_key: Optional[str] = None) -> Optional[T]:
        """Retrieve an item by its ID.
        
        Args:
            item_id: Unique identifier of the item
            partition_key: Partition key value (if required)
            
        Returns:
            The item if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_all(self, partition_key: Optional[str] = None) -> List[T]:
        """Retrieve all items.
        
        Args:
            partition_key: Partition key value to filter by
            
        Returns:
            List of all items
        """
        pass
    
    @abstractmethod
    async def query(self, filters: Dict[str, Any], partition_key: Optional[str] = None) -> List[T]:
        """Query items with filters.
        
        Args:
            filters: Dictionary of field-value pairs to filter by
            partition_key: Partition key value to filter by
            
        Returns:
            List of matching items
        """
        pass
    
    @abstractmethod
    async def create(self, item: T) -> T:
        """Create a new item.
        
        Args:
            item: The item to create
            
        Returns:
            The created item
            
        Raises:
            DuplicateItemException: If item already exists
        """
        pass
    
    @abstractmethod
    async def update(self, item_id: str, item: T, partition_key: Optional[str] = None) -> T:
        """Update an existing item.
        
        Args:
            item_id: ID of the item to update
            item: The updated item data
            partition_key: Partition key value
            
        Returns:
            The updated item
            
        Raises:
            ItemNotFoundException: If item doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete(self, item_id: str, partition_key: Optional[str] = None) -> bool:
        """Delete an item.
        
        Args:
            item_id: ID of the item to delete
            partition_key: Partition key value
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, item_id: str, partition_key: Optional[str] = None) -> bool:
        """Check if an item exists.
        
        Args:
            item_id: ID of the item to check
            partition_key: Partition key value
            
        Returns:
            True if item exists, False otherwise
        """
        pass


class CosmosRepositoryBase(IPortfolioRepository[T], ABC):
    """Base class for Cosmos DB repositories.
    
    Provides common functionality for all Cosmos DB repositories.
    """
    
    def __init__(self, container: ContainerProxy, model_class: type):
        """Initialize the repository.
        
        Args:
            container: Cosmos DB container proxy
            model_class: The Pydantic model class for this repository
        """
        self.container = container
        self.model_class = model_class
    
    async def get_by_id(self, item_id: str, partition_key: Optional[str] = None) -> Optional[T]:
        """Retrieve an item by ID from Cosmos DB."""
        try:
            if partition_key is None:
                partition_key = item_id
            
            item_data = self.container.read_item(
                item=item_id,
                partition_key=partition_key
            )
            return self._from_cosmos(item_data)
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error retrieving item {item_id}: {e}")
            raise RepositoryException(f"Failed to retrieve item: {e}")
    
    async def get_all(self, partition_key: Optional[str] = None) -> List[T]:
        """Retrieve all items from Cosmos DB."""
        try:
            query = "SELECT * FROM c"
            parameters = []
            
            if partition_key:
                # Query within specific partition
                items = self.container.query_items(
                    query=query,
                    partition_key=partition_key,
                    enable_cross_partition_query=False
                )
            else:
                # Cross-partition query
                items = self.container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                )
            
            return [self._from_cosmos(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error retrieving all items: {e}")
            raise RepositoryException(f"Failed to retrieve items: {e}")
    
    async def query(self, filters: Dict[str, Any], partition_key: Optional[str] = None) -> List[T]:
        """Query items with filters."""
        try:
            # Build query
            conditions = []
            parameters = []
            
            for i, (field, value) in enumerate(filters.items()):
                param_name = f"@param{i}"
                conditions.append(f"c.{field} = {param_name}")
                parameters.append({"name": param_name, "value": value})
            
            query = "SELECT * FROM c"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # Execute query
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=partition_key,
                enable_cross_partition_query=(partition_key is None)
            )
            
            return [self._from_cosmos(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error querying items: {e}")
            raise RepositoryException(f"Failed to query items: {e}")
    
    async def create(self, item: T) -> T:
        """Create a new item in Cosmos DB."""
        try:
            item_dict = self._to_cosmos(item)
            created_item = self.container.create_item(body=item_dict)
            return self._from_cosmos(created_item)
            
        except exceptions.CosmosResourceExistsError:
            raise DuplicateItemException(f"Item with ID {item.id} already exists")
        except Exception as e:
            logger.error(f"Error creating item: {e}")
            raise RepositoryException(f"Failed to create item: {e}")
    
    async def update(self, item_id: str, item: T, partition_key: Optional[str] = None) -> T:
        """Update an existing item in Cosmos DB."""
        try:
            if partition_key is None:
                partition_key = item_id
            
            # Ensure updated_at is set
            if hasattr(item, 'updated_at'):
                item.updated_at = datetime.utcnow()
            elif hasattr(item, 'last_updated'):
                item.last_updated = datetime.utcnow()
            
            item_dict = self._to_cosmos(item)
            updated_item = self.container.replace_item(
                item=item_id,
                body=item_dict
            )
            return self._from_cosmos(updated_item)
            
        except exceptions.CosmosResourceNotFoundError:
            raise ItemNotFoundException(f"Item with ID {item_id} not found")
        except Exception as e:
            logger.error(f"Error updating item {item_id}: {e}")
            raise RepositoryException(f"Failed to update item: {e}")
    
    async def delete(self, item_id: str, partition_key: Optional[str] = None) -> bool:
        """Delete an item from Cosmos DB."""
        try:
            if partition_key is None:
                partition_key = item_id
            
            self.container.delete_item(
                item=item_id,
                partition_key=partition_key
            )
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error deleting item {item_id}: {e}")
            raise RepositoryException(f"Failed to delete item: {e}")
    
    async def exists(self, item_id: str, partition_key: Optional[str] = None) -> bool:
        """Check if an item exists in Cosmos DB."""
        try:
            item = await self.get_by_id(item_id, partition_key)
            return item is not None
        except Exception as e:
            logger.error(f"Error checking if item exists {item_id}: {e}")
            return False
    
    def _to_cosmos(self, item: T) -> dict:
        """Convert domain model to Cosmos DB document.
        
        Subclasses can override this for custom serialization.
        """
        if hasattr(item, 'to_dict'):
            return item.to_dict()
        return item.model_dump()
    
    def _from_cosmos(self, data: dict) -> T:
        """Convert Cosmos DB document to domain model.
        
        Subclasses can override this for custom deserialization.
        """
        if hasattr(self.model_class, 'from_dict'):
            return self.model_class.from_dict(data)
        return self.model_class(**data)


class CosmosHoldingsRepository(CosmosRepositoryBase[Holding]):
    """Repository for managing holdings in Cosmos DB."""
    
    def __init__(self, container: ContainerProxy):
        """Initialize holdings repository."""
        super().__init__(container, Holding)
    
    async def get_by_ticker(self, ticker: str, portfolio_id: str = "default") -> List[Holding]:
        """Get all holdings for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            portfolio_id: Portfolio ID
            
        Returns:
            List of holdings for the ticker
        """
        return await self.query({"ticker": ticker.upper()}, partition_key=portfolio_id)
    
    async def get_portfolio_holdings(self, portfolio_id: str = "default") -> List[Holding]:
        """Get all holdings for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            List of all holdings in the portfolio
        """
        return await self.get_all(partition_key=portfolio_id)


class CosmosTransactionsRepository(CosmosRepositoryBase[Transaction]):
    """Repository for managing transactions in Cosmos DB."""
    
    def __init__(self, container: ContainerProxy):
        """Initialize transactions repository."""
        super().__init__(container, Transaction)
    
    async def get_by_ticker(self, ticker: str, portfolio_id: str = "default") -> List[Transaction]:
        """Get all transactions for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            portfolio_id: Portfolio ID
            
        Returns:
            List of transactions for the ticker
        """
        return await self.query({"ticker": ticker.upper()}, partition_key=portfolio_id)
    
    async def get_portfolio_transactions(self, portfolio_id: str = "default") -> List[Transaction]:
        """Get all transactions for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            List of all transactions in the portfolio
        """
        return await self.get_all(partition_key=portfolio_id)


class CosmosWatchlistsRepository(CosmosRepositoryBase[Watchlist]):
    """Repository for managing watchlists in Cosmos DB."""
    
    def __init__(self, container: ContainerProxy):
        """Initialize watchlists repository."""
        super().__init__(container, Watchlist)
    
    async def get_user_watchlists(self, user_id: str = "default") -> List[Watchlist]:
        """Get all watchlists for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of all watchlists for the user
        """
        return await self.get_all(partition_key=user_id)
    
    async def find_by_name(self, name: str, user_id: str = "default") -> Optional[Watchlist]:
        """Find a watchlist by name.
        
        Args:
            name: Watchlist name
            user_id: User ID
            
        Returns:
            Watchlist if found, None otherwise
        """
        results = await self.query({"name": name}, partition_key=user_id)
        return results[0] if results else None


class CosmosPortfolioRepository(CosmosRepositoryBase[Portfolio]):
    """Repository for managing portfolio state in Cosmos DB."""
    
    def __init__(self, container: ContainerProxy):
        """Initialize portfolio repository."""
        super().__init__(container, Portfolio)
    
    async def get_default_portfolio(self) -> Optional[Portfolio]:
        """Get the default portfolio.
        
        Returns:
            Default portfolio if it exists, None otherwise
        """
        return await self.get_by_id("default", partition_key="default")
    
    async def create_default_portfolio(self) -> Portfolio:
        """Create the default portfolio if it doesn't exist.
        
        Returns:
            The default portfolio
        """
        portfolio = Portfolio(id="default")
        try:
            return await self.create(portfolio)
        except DuplicateItemException:
            existing = await self.get_default_portfolio()
            if existing:
                return existing
            raise
