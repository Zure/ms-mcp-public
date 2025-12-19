from fastmcp import FastMCP
import logging
import asyncio
from finance_tools import (
	HistoryResponse,
	QuoteResponse,
	fetch_history,
	fetch_quote,
)

mcp = FastMCP(
	name="MSLab/Finance",
	version="0.1.0",
	instructions="Fetch quotes and historical prices from Yahoo Finance via yfinance.",
)

@mcp.tool(
	name="ping",
	description="A simple ping tool to test connectivity.",
)
def ping() -> str:
	return "pong"

@mcp.tool(
	name="get_quote",
	description="Fetch the latest available Yahoo Finance quote for a ticker symbol.",
)
def get_quote(ticker: str) -> QuoteResponse:
	return fetch_quote(ticker)


@mcp.tool(
	name="get_history",
	description=(
		"Download OHLCV price history for a ticker. Provide either a Yahoo Finance period string "
		"(e.g. '1mo', '6mo') or explicit ISO start/end dates."
	),
)
def get_history(
	ticker: str,
	*,
	period: str | None = None,
	start: str | None = None,
	end: str | None = None,
	interval: str = "1d",
) -> HistoryResponse:
	return fetch_history(
		ticker,
		period=period,
		start=start,
		end=end,
		interval=interval,
	)


if __name__ == "__main__":
	# Run the MCP server over stdio when executed directly.
	mcp.run(transport="stdio")
