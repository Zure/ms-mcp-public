"""Portfolio management tools for the MCP server.

This module contains all tool definitions for portfolio operations including:
- Adding and removing holdings
- Updating positions
- Viewing holdings and transaction history
"""

import logging
from typing import Optional
from fastmcp import FastMCP

from services.portfolio_service import PortfolioService, InsufficientFundsError
from services.validators import ValidationError

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, get_portfolio_service):
    """Register all portfolio management tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance
        get_portfolio_service: Async function that returns the PortfolioService instance
    """
    
    @mcp.tool()
    async def add_to_portfolio(
        ticker: str,
        quantity: int,
        purchase_price: float,
        purchase_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        """Add a new stock holding to the portfolio.
        
        Purchases shares of a stock, creates a holding record, logs a BUY transaction,
        and deducts the cost from the cash balance.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT'). Will be converted to uppercase.
            quantity: Number of shares to purchase (must be positive integer)
            purchase_price: Price per share (must be positive)
            purchase_date: Purchase date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
                          Defaults to current date/time if not provided.
            notes: Optional notes about the purchase (max 1000 characters)
        
        Returns:
            dict: Contains:
                - success: True if successful
                - holding: Created holding details
                - transaction: Created transaction details
                - total_cost: Total amount paid
                - new_cash_balance: Updated cash balance
        
        Raises:
            ValidationError: If inputs are invalid (invalid ticker format, negative values, etc.)
            InsufficientFundsError: If cash balance is insufficient for the purchase
        
        Example:
            add_to_portfolio(
                ticker="AAPL",
                quantity=10,
                purchase_price=150.50,
                notes="Long-term investment"
            )
        """
        try:
            service = await get_portfolio_service()
            result = await service.add_holding(
                ticker=ticker,
                quantity=float(quantity),
                purchase_price=purchase_price,
                purchase_date=purchase_date,
                notes=notes
            )
            return result
        except ValidationError as e:
            logger.warning(f"Validation error in add_to_portfolio: {e}")
            return {"success": False, "error": "validation_error", "message": str(e)}
        except InsufficientFundsError as e:
            logger.warning(f"Insufficient funds in add_to_portfolio: {e}")
            return {"success": False, "error": "insufficient_funds", "message": str(e)}
        except Exception as e:
            logger.error(f"Error in add_to_portfolio: {e}", exc_info=True)
            return {"success": False, "error": "internal_error", "message": str(e)}

    @mcp.tool()
    async def remove_from_portfolio(
        position_id: str,
        quantity: Optional[int] = None
    ) -> dict:
        """Remove a stock holding (full or partial) from the portfolio.
        
        Sells shares from a holding, creates a SELL transaction, and adds proceeds
        to the cash balance. If quantity is not specified, sells the entire position.
        
        Args:
            position_id: Unique identifier of the holding to sell
            quantity: Number of shares to sell. If None or not provided, sells entire position.
                     Cannot exceed the number of shares held.
        
        Returns:
            dict: Contains:
                - success: True if successful
                - transaction: Created transaction details
                - quantity_sold: Number of shares sold
                - proceeds: Total amount received from sale
                - new_cash_balance: Updated cash balance
                - holding_removed: True if entire position was sold
                - remaining_quantity: Shares remaining (0 if fully sold)
        
        Raises:
            ValidationError: If position_id is invalid or quantity exceeds holding
            ItemNotFoundException: If holding with position_id not found
        
        Example:
            # Sell 5 shares
            remove_from_portfolio(position_id="abc-123", quantity=5)
            
            # Sell entire position
            remove_from_portfolio(position_id="abc-123")
        """
        try:
            service = await get_portfolio_service()
            result = await service.remove_holding(
                position_id=position_id,
                quantity=float(quantity) if quantity is not None else None
            )
            return result
        except ValidationError as e:
            logger.warning(f"Validation error in remove_from_portfolio: {e}")
            return {"success": False, "error": "validation_error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error in remove_from_portfolio: {e}", exc_info=True)
            return {"success": False, "error": "internal_error", "message": str(e)}

    @mcp.tool()
    async def update_position(
        position_id: str,
        notes: Optional[str] = None,
        purchase_price: Optional[float] = None
    ) -> dict:
        """Update details of an existing holding.
        
        Allows updating the notes or purchase price (for cost basis adjustments) of a holding.
        At least one field must be provided for update.
        
        Args:
            position_id: Unique identifier of the holding to update
            notes: New notes for the holding (max 1000 characters). Use empty string to clear.
            purchase_price: New purchase price for cost basis adjustment (must be positive)
        
        Returns:
            dict: Contains:
                - success: True if successful
                - holding: Updated holding details
        
        Raises:
            ValidationError: If position_id is invalid, no fields provided, or values invalid
            ItemNotFoundException: If holding with position_id not found
        
        Example:
            update_position(
                position_id="abc-123",
                notes="Increased position based on Q4 earnings",
                purchase_price=155.75
            )
        """
        try:
            service = await get_portfolio_service()
            result = await service.update_position(
                position_id=position_id,
                notes=notes,
                purchase_price=purchase_price
            )
            return result
        except ValidationError as e:
            logger.warning(f"Validation error in update_position: {e}")
            return {"success": False, "error": "validation_error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error in update_position: {e}", exc_info=True)
            return {"success": False, "error": "internal_error", "message": str(e)}

    @mcp.tool()
    async def get_holdings(
        filter_ticker: Optional[str] = None,
        include_totals: bool = True
    ) -> dict:
        """Get all portfolio holdings with optional filtering and totals.
        
        Retrieves holdings from the portfolio, optionally filtered by ticker symbol.
        Can include portfolio totals such as total invested, cash balance, and per-ticker summaries.
        
        Args:
            filter_ticker: Filter results to specific ticker symbol (e.g., 'AAPL').
                          If None, returns all holdings.
            include_totals: If True, includes portfolio totals and per-ticker aggregations.
        
        Returns:
            dict: Contains:
                - holdings: List of holding objects
                - count: Number of holdings returned
                - totals (if include_totals=True):
                    - total_invested: Total amount invested across all holdings
                    - cash_balance: Available cash balance
                    - total_portfolio_value: Sum of invested + cash
                    - by_ticker: Per-ticker quantity and investment totals
        
        Example:
            # Get all holdings with totals
            get_holdings()
            
            # Get only AAPL holdings
            get_holdings(filter_ticker="AAPL", include_totals=False)
        """
        try:
            service = await get_portfolio_service()
            result = await service.get_holdings(
                filter_ticker=filter_ticker,
                include_totals=include_totals
            )
            return result
        except ValidationError as e:
            logger.warning(f"Validation error in get_holdings: {e}")
            return {"success": False, "error": "validation_error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error in get_holdings: {e}", exc_info=True)
            return {"success": False, "error": "internal_error", "message": str(e)}

    @mcp.tool()
    async def get_transaction_history(
        ticker: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 50
    ) -> dict:
        """Get transaction history with optional filtering.
        
        Retrieves transaction history, sorted by date (newest first), with optional filters
        for ticker, date range, and transaction type.
        
        Args:
            ticker: Filter by stock ticker symbol (e.g., 'AAPL')
            start_date: Filter transactions on or after this date (ISO format: YYYY-MM-DD)
            end_date: Filter transactions on or before this date (ISO format: YYYY-MM-DD)
            transaction_type: Filter by type: 'BUY', 'SELL', 'DIVIDEND', 'SPLIT', etc.
            limit: Maximum number of results to return (default 50, max 200)
        
        Returns:
            dict: Contains:
                - transactions: List of transaction objects (newest first)
                - count: Number of transactions returned
                - filters: Echo of applied filters
        
        Raises:
            ValidationError: If date format or transaction type is invalid
        
        Example:
            # Get last 10 transactions
            get_transaction_history(limit=10)
            
            # Get AAPL buy transactions in 2024
            get_transaction_history(
                ticker="AAPL",
                transaction_type="BUY",
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
        """
        try:
            service = await get_portfolio_service()
            result = await service.get_transaction_history(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                limit=limit
            )
            return result
        except ValidationError as e:
            logger.warning(f"Validation error in get_transaction_history: {e}")
            return {"success": False, "error": "validation_error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error in get_transaction_history: {e}", exc_info=True)
            return {"success": False, "error": "internal_error", "message": str(e)}
    
    logger.info("✅ Portfolio tools registered successfully")
