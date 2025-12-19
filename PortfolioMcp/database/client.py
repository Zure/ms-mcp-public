"""Database client interface and Cosmos DB implementation.

This module provides an abstraction layer for database operations,
allowing for easy migration to different database providers in the future.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging
import time
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy, exceptions
from azure.cosmos.partition_key import PartitionKey

logger = logging.getLogger(__name__)


class DatabaseException(Exception):
    """Base exception for database operations."""
    pass


class ConnectionException(DatabaseException):
    """Exception raised when database connection fails."""
    pass


class QueryException(DatabaseException):
    """Exception raised when query execution fails."""
    pass


class IPortfolioDatabaseClient(ABC):
    """Abstract interface for portfolio database client.
    
    This interface allows for different database implementations
    (Cosmos DB, MongoDB, PostgreSQL, etc.) to be swapped easily.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the database.
        
        Raises:
            ConnectionException: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the database."""
        pass
    
    @abstractmethod
    def get_container(self, container_name: str) -> Any:
        """Get a reference to a database container/collection.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Container reference
            
        Raises:
            DatabaseException: If container access fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Verify database connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def initialize_database(self) -> None:
        """Initialize database schema (containers, indexes, etc.).
        
        Raises:
            DatabaseException: If initialization fails
        """
        pass


class CosmosDBClient(IPortfolioDatabaseClient):
    """Cosmos DB implementation of the database client.
    
    Supports both Azure Cosmos DB and the Cosmos DB emulator for development.
    
    Attributes:
        endpoint: Cosmos DB endpoint URL
        key: Cosmos DB access key
        database_name: Name of the database
        client: Cosmos DB client instance
        database: Database proxy instance
    """
    
    def __init__(
        self,
        endpoint: str,
        key: str,
        database_name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize Cosmos DB client.
        
        Args:
            endpoint: Cosmos DB endpoint URL
            key: Cosmos DB access key
            database_name: Name of the database
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
        """
        self.endpoint = endpoint
        self.key = key
        self.database_name = database_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self._connected = False
        
        # Container definitions
        self._containers = {
            "holdings": "/portfolio_id",
            "transactions": "/portfolio_id",
            "watchlists": "/user_id",
            "portfolios": "/id"
        }
    
    async def connect(self) -> None:
        """Establish connection to Cosmos DB.
        
        Raises:
            ConnectionException: If connection fails after retries
        """
        if self._connected:
            logger.debug("Already connected to Cosmos DB")
            return
        
        logger.info(f"Connecting to Cosmos DB at {self.endpoint}")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Initialize Cosmos client
                self.client = CosmosClient(
                    self.endpoint,
                    self.key,
                    connection_verify=self._should_verify_ssl()
                )
                
                # Get or create database
                self.database = self.client.create_database_if_not_exists(
                    id=self.database_name
                )
                
                self._connected = True
                logger.info(f"✅ Connected to Cosmos DB database: {self.database_name}")
                return
                
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Cosmos DB connection failed (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise ConnectionException(
                        f"Failed to connect to Cosmos DB after {self.max_retries} attempts: {e}"
                    )
            except Exception as e:
                logger.error(f"Unexpected error connecting to Cosmos DB: {e}")
                raise ConnectionException(f"Failed to connect to Cosmos DB: {e}")
    
    async def disconnect(self) -> None:
        """Close connection to Cosmos DB."""
        if self.client:
            logger.info("Disconnecting from Cosmos DB")
            # Cosmos client doesn't require explicit closing
            self.client = None
            self.database = None
            self._connected = False
            logger.info("✅ Disconnected from Cosmos DB")
    
    def get_container(self, container_name: str) -> ContainerProxy:
        """Get a reference to a Cosmos DB container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            ContainerProxy: Container reference
            
        Raises:
            DatabaseException: If container access fails
        """
        if not self._connected or not self.database:
            raise DatabaseException("Not connected to database. Call connect() first.")
        
        try:
            container = self.database.get_container_client(container_name)
            return container
        except Exception as e:
            raise DatabaseException(f"Failed to get container '{container_name}': {e}")
    
    async def health_check(self) -> bool:
        """Verify Cosmos DB connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self._connected or not self.database:
                return False
            
            # Try to read database properties
            self.database.read()
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def initialize_database(self) -> None:
        """Initialize Cosmos DB containers and indexes.
        
        Checks if containers exist and creates them if they don't.
        Reports on the status of each container (existing or newly created).
        
        Raises:
            DatabaseException: If initialization fails
        """
        if not self._connected or not self.database:
            raise DatabaseException("Not connected to database. Call connect() first.")
        
        logger.info("🔍 Checking Cosmos DB containers...")
        
        try:
            created_count = 0
            existing_count = 0
            
            for container_name, partition_key_path in self._containers.items():
                try:
                    # Check if container already exists
                    container_exists = await self._check_container_exists(container_name)
                    
                    if container_exists:
                        logger.info(f"✓ Container '{container_name}' already exists")
                        existing_count += 1
                    else:
                        logger.info(f"📦 Creating container '{container_name}' with partition key {partition_key_path}...")
                        
                    # Create container if it doesn't exist
                    container = self.database.create_container_if_not_exists(
                        id=container_name,
                        partition_key=PartitionKey(path=partition_key_path),
                        offer_throughput=400  # Minimum throughput for development
                    )
                    
                    if not container_exists:
                        logger.info(f"✅ Container '{container_name}' created successfully")
                        created_count += 1
                    
                except exceptions.CosmosHttpResponseError as e:
                    logger.error(f"❌ Failed to initialize container '{container_name}': {e}")
                    raise DatabaseException(f"Failed to initialize container '{container_name}': {e}")
            
            # Summary
            logger.info("=" * 60)
            logger.info(f"📊 Container Status Summary:")
            logger.info(f"   - Existing containers: {existing_count}")
            logger.info(f"   - Newly created containers: {created_count}")
            logger.info(f"   - Total containers: {len(self._containers)}")
            logger.info("✅ All containers ready")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise DatabaseException(f"Database initialization failed: {e}")
    
    async def _check_container_exists(self, container_name: str) -> bool:
        """Check if a container exists in the database.
        
        Args:
            container_name: Name of the container to check
            
        Returns:
            bool: True if container exists, False otherwise
        """
        try:
            container_list = list(self.database.list_containers())
            return any(c['id'] == container_name for c in container_list)
        except Exception as e:
            logger.warning(f"Could not check if container exists: {e}")
            return False
    
    def _should_verify_ssl(self) -> bool:
        """Determine if SSL verification should be enabled.
        
        For Cosmos DB emulator (localhost), SSL verification is disabled.
        
        Returns:
            bool: True if SSL should be verified, False otherwise
        """
        is_emulator = "localhost" in self.endpoint or "127.0.0.1" in self.endpoint
        if is_emulator:
            logger.warning("⚠️  SSL verification disabled for Cosmos DB emulator")
        return not is_emulator
