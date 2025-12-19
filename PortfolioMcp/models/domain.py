"""Domain models for portfolio management.

These Pydantic models define the core data structures used throughout
the application for holdings, transactions, watchlists, and portfolios.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class TransactionType(str, Enum):
    """Types of portfolio transactions."""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


class Holding(BaseModel):
    """Represents a stock holding in the portfolio.
    
    Attributes:
        id: Unique identifier for the holding
        portfolio_id: ID of the portfolio this holding belongs to
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        quantity: Number of shares held
        purchase_price: Average purchase price per share
        purchase_date: Date of initial purchase
        notes: Optional notes about the holding
        created_at: Timestamp when the holding was created
        updated_at: Timestamp when the holding was last updated
    """
    id: str
    portfolio_id: str = "default"  # For future multi-portfolio support
    ticker: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)
    purchase_date: datetime
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase."""
        return v.upper()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for storage."""
        data = self.model_dump()
        # Convert datetime to ISO format strings
        for key in ['purchase_date', 'created_at', 'updated_at']:
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Holding":
        """Create model from dictionary."""
        # Convert ISO format strings to datetime
        for key in ['purchase_date', 'created_at', 'updated_at']:
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)
    
    def calculate_value(self, current_price: float) -> float:
        """Calculate current value of the holding."""
        return self.quantity * current_price
    
    def calculate_gain_loss(self, current_price: float) -> float:
        """Calculate gain/loss on the holding."""
        return (current_price - self.purchase_price) * self.quantity
    
    def calculate_gain_loss_percent(self, current_price: float) -> float:
        """Calculate gain/loss percentage."""
        return ((current_price - self.purchase_price) / self.purchase_price) * 100


class Transaction(BaseModel):
    """Represents a transaction in the portfolio.
    
    Attributes:
        id: Unique identifier for the transaction
        portfolio_id: ID of the portfolio this transaction belongs to
        type: Type of transaction (buy, sell, dividend, etc.)
        ticker: Stock ticker symbol (optional for some transaction types)
        quantity: Number of shares (optional for some transaction types)
        price: Price per share
        total: Total transaction amount
        date: Date of the transaction
        notes: Optional notes about the transaction
        created_at: Timestamp when the transaction was recorded
    """
    id: str
    portfolio_id: str = "default"
    type: TransactionType
    ticker: Optional[str] = Field(None, min_length=1, max_length=10)
    quantity: Optional[float] = Field(None, gt=0)
    price: float = Field(..., ge=0)
    total: float
    date: datetime
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """Ensure ticker is uppercase if provided."""
        return v.upper() if v else v
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for storage."""
        data = self.model_dump()
        # Convert datetime to ISO format strings
        for key in ['date', 'created_at']:
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        # Convert enum to string
        if isinstance(data['type'], TransactionType):
            data['type'] = data['type'].value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Create model from dictionary."""
        # Convert ISO format strings to datetime
        for key in ['date', 'created_at']:
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        # Convert string to enum
        if 'type' in data and isinstance(data['type'], str):
            data['type'] = TransactionType(data['type'])
        return cls(**data)


class Watchlist(BaseModel):
    """Represents a watchlist of stocks to monitor.
    
    Attributes:
        id: Unique identifier for the watchlist
        user_id: ID of the user who owns the watchlist
        name: Name of the watchlist
        tickers: List of stock ticker symbols
        notes: Optional notes about the watchlist
        created_at: Timestamp when the watchlist was created
        updated_at: Timestamp when the watchlist was last updated
    """
    id: str
    user_id: str = "default"  # For future multi-user support
    name: str = Field(..., min_length=1, max_length=100)
    tickers: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('tickers')
    @classmethod
    def tickers_uppercase(cls, v: List[str]) -> List[str]:
        """Ensure all tickers are uppercase."""
        return [ticker.upper() for ticker in v]
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for storage."""
        data = self.model_dump()
        # Convert datetime to ISO format strings
        for key in ['created_at', 'updated_at']:
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Watchlist":
        """Create model from dictionary."""
        # Convert ISO format strings to datetime
        for key in ['created_at', 'updated_at']:
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)
    
    def add_ticker(self, ticker: str) -> None:
        """Add a ticker to the watchlist if not already present."""
        ticker = ticker.upper()
        if ticker not in self.tickers:
            self.tickers.append(ticker)
            self.updated_at = datetime.utcnow()
    
    def remove_ticker(self, ticker: str) -> bool:
        """Remove a ticker from the watchlist. Returns True if removed."""
        ticker = ticker.upper()
        if ticker in self.tickers:
            self.tickers.remove(ticker)
            self.updated_at = datetime.utcnow()
            return True
        return False


class Portfolio(BaseModel):
    """Represents the overall portfolio state.
    
    Attributes:
        id: Unique identifier for the portfolio
        cash_balance: Available cash balance
        last_updated: Timestamp of last update
        created_at: Timestamp when the portfolio was created
    """
    id: str = "default"
    cash_balance: float = Field(default=0.0, ge=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for storage."""
        data = self.model_dump()
        # Convert datetime to ISO format strings
        for key in ['last_updated', 'created_at']:
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        """Create model from dictionary."""
        # Convert ISO format strings to datetime
        for key in ['last_updated', 'created_at']:
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)
    
    def add_cash(self, amount: float) -> None:
        """Add cash to the portfolio."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.cash_balance += amount
        self.last_updated = datetime.utcnow()
    
    def withdraw_cash(self, amount: float) -> None:
        """Withdraw cash from the portfolio."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.cash_balance:
            raise ValueError("Insufficient cash balance")
        self.cash_balance -= amount
        self.last_updated = datetime.utcnow()
