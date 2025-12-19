"""Portfolio service for business logic and orchestration.

This module provides the main service layer for portfolio management,
coordinating between repositories, validation, and business rules.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from database.repository import (
    CosmosHoldingsRepository,
    CosmosTransactionsRepository,
    CosmosPortfolioRepository,
    ItemNotFoundException,
    RepositoryException
)
from models.domain import Holding, Transaction, Portfolio, TransactionType
from services.validators import PortfolioValidator, ValidationError

logger = logging.getLogger(__name__)


class InsufficientFundsError(Exception):
    """Raised when there are insufficient funds for an operation."""
    pass


class PortfolioService:
    """Service for portfolio management operations.
    
    This service provides high-level business logic for portfolio operations,
    including holdings management, transaction tracking, and cash balance management.
    """
    
    def __init__(
        self,
        holdings_repo: CosmosHoldingsRepository,
        transactions_repo: CosmosTransactionsRepository,
        portfolio_repo: CosmosPortfolioRepository
    ):
        """Initialize the portfolio service.
        
        Args:
            holdings_repo: Repository for holdings data
            transactions_repo: Repository for transactions data
            portfolio_repo: Repository for portfolio state
        """
        self.holdings_repo = holdings_repo
        self.transactions_repo = transactions_repo
        self.portfolio_repo = portfolio_repo
        self.validator = PortfolioValidator()
    
    async def get_or_create_portfolio(self, portfolio_id: str = "default") -> Portfolio:
        """Get or create a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            The portfolio
        """
        portfolio = await self.portfolio_repo.get_by_id(portfolio_id, portfolio_id)
        if portfolio is None:
            portfolio = Portfolio(id=portfolio_id, cash_balance=100000.0)  # Default $100k starting balance
            portfolio = await self.portfolio_repo.create(portfolio)
            logger.info(f"Created new portfolio {portfolio_id} with cash balance {portfolio.cash_balance}")
        return portfolio
    
    async def get_cash_balance(self, portfolio_id: str = "default") -> float:
        """Get the current cash balance for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Current cash balance
        """
        portfolio = await self.get_or_create_portfolio(portfolio_id)
        return portfolio.cash_balance
    
    async def update_cash_balance(
        self,
        amount: float,
        operation: str,
        portfolio_id: str = "default"
    ) -> float:
        """Update the cash balance for a portfolio.
        
        Args:
            amount: Amount to add or subtract (must be positive)
            operation: "add" or "subtract"
            portfolio_id: Portfolio identifier
            
        Returns:
            New cash balance
            
        Raises:
            ValidationError: If amount or operation is invalid
            InsufficientFundsError: If subtracting more than available balance
        """
        if amount < 0:
            raise ValidationError("Amount must be positive")
        
        if operation not in ["add", "subtract"]:
            raise ValidationError(f"Invalid operation: {operation}. Must be 'add' or 'subtract'")
        
        portfolio = await self.get_or_create_portfolio(portfolio_id)
        
        if operation == "add":
            portfolio.add_cash(amount)
        else:  # subtract
            if amount > portfolio.cash_balance:
                raise InsufficientFundsError(
                    f"Insufficient funds: tried to withdraw {amount}, "
                    f"but only {portfolio.cash_balance} available"
                )
            portfolio.withdraw_cash(amount)
        
        # Save updated portfolio
        await self.portfolio_repo.update(portfolio_id, portfolio, portfolio_id)
        logger.info(f"Updated cash balance for portfolio {portfolio_id}: {operation} {amount}, new balance: {portfolio.cash_balance}")
        
        return portfolio.cash_balance
    
    async def add_holding(
        self,
        ticker: str,
        quantity: float,
        purchase_price: float,
        purchase_date: Optional[str] = None,
        notes: Optional[str] = None,
        portfolio_id: str = "default"
    ) -> Dict[str, Any]:
        """Add a new holding to the portfolio.
        
        Args:
            ticker: Stock ticker symbol
            quantity: Number of shares to purchase
            purchase_price: Price per share
            purchase_date: Purchase date (ISO format, defaults to now)
            notes: Optional notes about the purchase
            portfolio_id: Portfolio identifier
            
        Returns:
            Dictionary with holding details and transaction info
            
        Raises:
            ValidationError: If inputs are invalid
            InsufficientFundsError: If insufficient cash balance
        """
        # Validate inputs
        ticker = self.validator.validate_ticker(ticker)
        quantity = self.validator.validate_quantity(quantity)
        purchase_price = self.validator.validate_price(purchase_price)
        purchase_date_dt = self.validator.validate_date(purchase_date)
        notes = self.validator.validate_notes(notes)
        
        # Calculate total cost
        total_cost = quantity * purchase_price
        
        # Check cash balance
        current_balance = await self.get_cash_balance(portfolio_id)
        if total_cost > current_balance:
            raise InsufficientFundsError(
                f"Insufficient funds: purchase costs {total_cost}, "
                f"but only {current_balance} available"
            )
        
        try:
            # Create holding
            holding_id = str(uuid.uuid4())
            holding = Holding(
                id=holding_id,
                portfolio_id=portfolio_id,
                ticker=ticker,
                quantity=quantity,
                purchase_price=purchase_price,
                purchase_date=purchase_date_dt,
                notes=notes
            )
            
            created_holding = await self.holdings_repo.create(holding)
            logger.info(f"Created holding {holding_id}: {quantity} shares of {ticker} at {purchase_price}")
            
            # Create transaction
            transaction_id = str(uuid.uuid4())
            transaction = Transaction(
                id=transaction_id,
                portfolio_id=portfolio_id,
                type=TransactionType.BUY,
                ticker=ticker,
                quantity=quantity,
                price=purchase_price,
                total=-total_cost,  # Negative because it's money out
                date=purchase_date_dt,
                notes=f"Purchase of {quantity} shares at ${purchase_price}"
            )
            
            created_transaction = await self.transactions_repo.create(transaction)
            logger.info(f"Created BUY transaction {transaction_id} for {ticker}")
            
            # Update cash balance
            new_balance = await self.update_cash_balance(total_cost, "subtract", portfolio_id)
            
            return {
                "success": True,
                "holding": created_holding.to_dict(),
                "transaction": created_transaction.to_dict(),
                "total_cost": total_cost,
                "new_cash_balance": new_balance
            }
            
        except Exception as e:
            logger.error(f"Error adding holding: {e}")
            # Note: In a production system, implement proper transaction rollback
            raise
    
    async def remove_holding(
        self,
        position_id: str,
        quantity: Optional[float] = None,
        portfolio_id: str = "default"
    ) -> Dict[str, Any]:
        """Remove a holding (full or partial) from the portfolio.
        
        Args:
            position_id: ID of the holding to remove
            quantity: Number of shares to sell (None = sell all)
            portfolio_id: Portfolio identifier
            
        Returns:
            Dictionary with transaction details and proceeds
            
        Raises:
            ValidationError: If inputs are invalid
            ItemNotFoundException: If holding not found
        """
        # Validate position ID
        position_id = self.validator.validate_position_id(position_id)
        
        # Get the holding
        holding = await self.holdings_repo.get_by_id(position_id, portfolio_id)
        if holding is None:
            raise ItemNotFoundException(f"Holding with ID {position_id} not found")
        
        # Determine quantity to sell
        if quantity is None:
            quantity_to_sell = holding.quantity
            is_full_sale = True
        else:
            quantity_to_sell = self.validator.validate_quantity(quantity)
            if quantity_to_sell > holding.quantity:
                raise ValidationError(
                    f"Cannot sell {quantity_to_sell} shares: only {holding.quantity} shares held"
                )
            is_full_sale = (quantity_to_sell == holding.quantity)
        
        # Calculate proceeds (using original purchase price as current price for now)
        proceeds = quantity_to_sell * holding.purchase_price
        
        try:
            # Update or delete holding
            if is_full_sale:
                await self.holdings_repo.delete(position_id, portfolio_id)
                logger.info(f"Deleted holding {position_id}: sold all {quantity_to_sell} shares of {holding.ticker}")
            else:
                holding.quantity -= quantity_to_sell
                holding.updated_at = datetime.utcnow()
                await self.holdings_repo.update(position_id, holding, portfolio_id)
                logger.info(f"Updated holding {position_id}: sold {quantity_to_sell} shares of {holding.ticker}, {holding.quantity} remaining")
            
            # Create transaction
            transaction_id = str(uuid.uuid4())
            transaction = Transaction(
                id=transaction_id,
                portfolio_id=portfolio_id,
                type=TransactionType.SELL,
                ticker=holding.ticker,
                quantity=quantity_to_sell,
                price=holding.purchase_price,
                total=proceeds,  # Positive because it's money in
                date=datetime.utcnow(),
                notes=f"Sale of {quantity_to_sell} shares at ${holding.purchase_price}"
            )
            
            created_transaction = await self.transactions_repo.create(transaction)
            logger.info(f"Created SELL transaction {transaction_id} for {holding.ticker}")
            
            # Update cash balance
            new_balance = await self.update_cash_balance(proceeds, "add", portfolio_id)
            
            return {
                "success": True,
                "transaction": created_transaction.to_dict(),
                "quantity_sold": quantity_to_sell,
                "proceeds": proceeds,
                "new_cash_balance": new_balance,
                "holding_removed": is_full_sale,
                "remaining_quantity": 0 if is_full_sale else holding.quantity
            }
            
        except Exception as e:
            logger.error(f"Error removing holding: {e}")
            raise
    
    async def update_position(
        self,
        position_id: str,
        notes: Optional[str] = None,
        purchase_price: Optional[float] = None,
        portfolio_id: str = "default"
    ) -> Dict[str, Any]:
        """Update a holding's details.
        
        Args:
            position_id: ID of the holding to update
            notes: New notes (None = don't update)
            purchase_price: New purchase price for cost basis adjustment (None = don't update)
            portfolio_id: Portfolio identifier
            
        Returns:
            Dictionary with updated holding details
            
        Raises:
            ValidationError: If inputs are invalid
            ItemNotFoundException: If holding not found
        """
        # Validate position ID
        position_id = self.validator.validate_position_id(position_id)
        
        # Get the holding
        holding = await self.holdings_repo.get_by_id(position_id, portfolio_id)
        if holding is None:
            raise ItemNotFoundException(f"Holding with ID {position_id} not found")
        
        # Validate and update fields
        updated = False
        
        if notes is not None:
            notes = self.validator.validate_notes(notes)
            holding.notes = notes
            updated = True
        
        if purchase_price is not None:
            purchase_price = self.validator.validate_price(purchase_price)
            old_price = holding.purchase_price
            holding.purchase_price = purchase_price
            updated = True
            logger.info(f"Updated purchase price for holding {position_id}: {old_price} -> {purchase_price}")
        
        if not updated:
            raise ValidationError("No fields to update")
        
        # Update holding
        holding.updated_at = datetime.utcnow()
        updated_holding = await self.holdings_repo.update(position_id, holding, portfolio_id)
        
        return {
            "success": True,
            "holding": updated_holding.to_dict()
        }
    
    async def get_holdings(
        self,
        filter_ticker: Optional[str] = None,
        include_totals: bool = True,
        portfolio_id: str = "default"
    ) -> Dict[str, Any]:
        """Get portfolio holdings with optional filtering and totals.
        
        Args:
            filter_ticker: Filter by ticker symbol (None = all holdings)
            include_totals: Include portfolio totals
            portfolio_id: Portfolio identifier
            
        Returns:
            Dictionary with holdings and optional totals
        """
        # Get holdings
        if filter_ticker:
            filter_ticker = self.validator.validate_ticker(filter_ticker)
            holdings = await self.holdings_repo.get_by_ticker(filter_ticker, portfolio_id)
        else:
            holdings = await self.holdings_repo.get_portfolio_holdings(portfolio_id)
        
        result = {
            "holdings": [h.to_dict() for h in holdings],
            "count": len(holdings)
        }
        
        if include_totals:
            # Calculate totals
            total_invested = sum(h.quantity * h.purchase_price for h in holdings)
            cash_balance = await self.get_cash_balance(portfolio_id)
            
            # Group by ticker
            ticker_totals = {}
            for h in holdings:
                if h.ticker not in ticker_totals:
                    ticker_totals[h.ticker] = {"quantity": 0, "invested": 0}
                ticker_totals[h.ticker]["quantity"] += h.quantity
                ticker_totals[h.ticker]["invested"] += h.quantity * h.purchase_price
            
            result["totals"] = {
                "total_invested": total_invested,
                "cash_balance": cash_balance,
                "total_portfolio_value": total_invested + cash_balance,
                "by_ticker": ticker_totals
            }
        
        return result
    
    async def get_transaction_history(
        self,
        ticker: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 50,
        portfolio_id: str = "default"
    ) -> Dict[str, Any]:
        """Get transaction history with optional filtering.
        
        Args:
            ticker: Filter by ticker symbol
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            transaction_type: Filter by transaction type (BUY, SELL, etc.)
            limit: Maximum number of results (max 200)
            portfolio_id: Portfolio identifier
            
        Returns:
            Dictionary with filtered transactions
            
        Raises:
            ValidationError: If filters are invalid
        """
        # Validate filters
        if ticker:
            ticker = self.validator.validate_ticker(ticker)
        
        if transaction_type:
            transaction_type = self.validator.validate_transaction_type(transaction_type)
        
        start_dt = None
        if start_date:
            start_dt = self.validator.validate_date(start_date)
        
        end_dt = None
        if end_date:
            end_dt = self.validator.validate_date(end_date)
        
        # Limit validation
        limit = min(max(1, limit), 200)  # Ensure between 1 and 200
        
        # Get transactions
        if ticker:
            transactions = await self.transactions_repo.get_by_ticker(ticker, portfolio_id)
        else:
            transactions = await self.transactions_repo.get_portfolio_transactions(portfolio_id)
        
        # Apply filters
        filtered = transactions
        
        if transaction_type:
            filtered = [t for t in filtered if t.type.value.upper() == transaction_type]
        
        if start_dt:
            filtered = [t for t in filtered if t.date >= start_dt]
        
        if end_dt:
            filtered = [t for t in filtered if t.date <= end_dt]
        
        # Sort by date descending (newest first)
        filtered.sort(key=lambda t: t.date, reverse=True)
        
        # Apply limit
        filtered = filtered[:limit]
        
        return {
            "transactions": [t.to_dict() for t in filtered],
            "count": len(filtered),
            "filters": {
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "transaction_type": transaction_type,
                "limit": limit
            }
        }
