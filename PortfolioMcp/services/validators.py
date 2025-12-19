"""Validation utilities for portfolio management.

This module provides comprehensive validation for portfolio operations,
ensuring data integrity and providing clear error messages.
"""

import re
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class PortfolioValidator:
    """Validator for portfolio data and operations.
    
    Provides static methods for validating tickers, quantities, prices,
    dates, and transaction types used throughout the portfolio system.
    """
    
    # Valid ticker pattern: 1-10 uppercase letters, optionally followed by a dot and 1-3 letters
    TICKER_PATTERN = re.compile(r'^[A-Z]{1,10}(\.[A-Z]{1,3})?$')
    
    @staticmethod
    def validate_ticker(ticker: str) -> str:
        """Validate and normalize a stock ticker symbol.
        
        Args:
            ticker: Stock ticker symbol to validate
            
        Returns:
            Normalized ticker (uppercase)
            
        Raises:
            ValidationError: If ticker format is invalid
        """
        if not ticker:
            raise ValidationError("Ticker cannot be empty")
        
        # Convert to uppercase
        ticker = ticker.strip().upper()
        
        # Check pattern
        if not PortfolioValidator.TICKER_PATTERN.match(ticker):
            raise ValidationError(
                f"Invalid ticker format: '{ticker}'. "
                "Ticker must be 1-10 uppercase letters, optionally followed by a dot and 1-3 letters "
                "(e.g., 'AAPL', 'MSFT', 'BRK.B')"
            )
        
        return ticker
    
    @staticmethod
    def validate_quantity(quantity: float, allow_zero: bool = False) -> float:
        """Validate a quantity value.
        
        Args:
            quantity: Quantity to validate
            allow_zero: Whether to allow zero quantity
            
        Returns:
            The validated quantity
            
        Raises:
            ValidationError: If quantity is invalid
        """
        if quantity is None:
            raise ValidationError("Quantity cannot be None")
        
        if not isinstance(quantity, (int, float)):
            raise ValidationError(f"Quantity must be a number, got {type(quantity).__name__}")
        
        if quantity < 0:
            raise ValidationError(f"Quantity cannot be negative: {quantity}")
        
        if not allow_zero and quantity == 0:
            raise ValidationError("Quantity must be greater than zero")
        
        if quantity != int(quantity):
            raise ValidationError(f"Quantity must be a whole number: {quantity}")
        
        return float(quantity)
    
    @staticmethod
    def validate_price(price: float, allow_zero: bool = False) -> float:
        """Validate a price value.
        
        Args:
            price: Price to validate
            allow_zero: Whether to allow zero price
            
        Returns:
            The validated price
            
        Raises:
            ValidationError: If price is invalid
        """
        if price is None:
            raise ValidationError("Price cannot be None")
        
        if not isinstance(price, (int, float)):
            raise ValidationError(f"Price must be a number, got {type(price).__name__}")
        
        if price < 0:
            raise ValidationError(f"Price cannot be negative: {price}")
        
        if not allow_zero and price == 0:
            raise ValidationError("Price must be greater than zero")
        
        return float(price)
    
    @staticmethod
    def validate_date(date_str: Optional[str]) -> datetime:
        """Validate and parse a date string.
        
        Args:
            date_str: Date string in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
                     If None, returns current datetime
            
        Returns:
            Parsed datetime object
            
        Raises:
            ValidationError: If date format is invalid
        """
        if date_str is None:
            return datetime.utcnow()
        
        if not isinstance(date_str, str):
            raise ValidationError(f"Date must be a string, got {type(date_str).__name__}")
        
        # Try parsing ISO format
        try:
            # Handle both date-only and full datetime formats
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(date_str)
        except ValueError as e:
            raise ValidationError(
                f"Invalid date format: '{date_str}'. "
                "Expected ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
            )
    
    @staticmethod
    def validate_transaction_type(transaction_type: str) -> str:
        """Validate a transaction type.
        
        Args:
            transaction_type: Transaction type to validate
            
        Returns:
            Normalized transaction type (uppercase)
            
        Raises:
            ValidationError: If transaction type is invalid
        """
        if not transaction_type:
            raise ValidationError("Transaction type cannot be empty")
        
        valid_types = {"BUY", "SELL", "DIVIDEND", "SPLIT", "TRANSFER_IN", "TRANSFER_OUT"}
        transaction_type = transaction_type.strip().upper()
        
        if transaction_type not in valid_types:
            raise ValidationError(
                f"Invalid transaction type: '{transaction_type}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )
        
        return transaction_type
    
    @staticmethod
    def validate_notes(notes: Optional[str], max_length: int = 1000) -> Optional[str]:
        """Validate notes field.
        
        Args:
            notes: Notes text to validate
            max_length: Maximum allowed length
            
        Returns:
            Validated notes (or None)
            
        Raises:
            ValidationError: If notes are too long
        """
        if notes is None:
            return None
        
        if not isinstance(notes, str):
            raise ValidationError(f"Notes must be a string, got {type(notes).__name__}")
        
        notes = notes.strip()
        
        if not notes:
            return None
        
        if len(notes) > max_length:
            raise ValidationError(
                f"Notes too long: {len(notes)} characters (maximum {max_length})"
            )
        
        return notes
    
    @staticmethod
    def validate_position_id(position_id: str) -> str:
        """Validate a position ID.
        
        Args:
            position_id: Position ID to validate
            
        Returns:
            The validated position ID
            
        Raises:
            ValidationError: If position ID is invalid
        """
        if not position_id:
            raise ValidationError("Position ID cannot be empty")
        
        if not isinstance(position_id, str):
            raise ValidationError(f"Position ID must be a string, got {type(position_id).__name__}")
        
        position_id = position_id.strip()
        
        if not position_id:
            raise ValidationError("Position ID cannot be empty")
        
        return position_id
