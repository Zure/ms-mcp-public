from datetime import datetime, timezone
from typing import Any, TypedDict

import pandas as pd
import yfinance as yf
from fastmcp.exceptions import ToolError

ALLOWED_INTERVALS = {
    "1m",
    "2m",
    "5m",
    "15m",
    "30m",
    "60m",
    "90m",
    "1h",
    "1d",
    "5d",
    "1wk",
    "1mo",
    "3mo",
}
DEFAULT_PERIOD = "1mo"


class QuoteFields(TypedDict, total=False):
    last_price: float | None
    currency: str | None
    day_high: float | None
    day_low: float | None
    open: float | None
    previous_close: float | None
    volume: int | None
    market_cap: float | None


class QuoteResponse(QuoteFields):
    ticker: str
    timestamp: str


class HistoryPoint(TypedDict):
    timestamp: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    adj_close: float | None
    volume: int | None


class HistoryResponse(TypedDict):
    ticker: str
    interval: str
    period: str | None
    start: str | None
    end: str | None
    candles: list[HistoryPoint]


def _clean_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_int(value: Any) -> int | None:
    numeric = _clean_number(value)
    if numeric is None:
        return None
    return int(numeric)


def _normalize_ticker(raw: str) -> str:
    symbol = raw.strip().upper()
    if not symbol:
        raise ToolError("Ticker symbol is required.")
    return symbol


def _normalize_optional_str(raw: str | None) -> str | None:
    if raw is None:
        return None
    trimmed = raw.strip()
    return trimmed or None


def _current_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def _timestamp_to_iso(index_value: Any) -> str:
    if isinstance(index_value, pd.Timestamp):
        dt_value = index_value.to_pydatetime()
    elif isinstance(index_value, datetime):
        dt_value = index_value
    else:
        raise ToolError("Unexpected timestamp type returned by yfinance.")

    if dt_value.tzinfo is not None:
        dt_value = dt_value.astimezone(timezone.utc).replace(tzinfo=None)

    return dt_value.replace(microsecond=0).isoformat()


def _extract_fast_info(ticker: yf.Ticker) -> dict[str, Any]:
    fast_info = ticker.fast_info
    snapshot: dict[str, Any] = {}
    try:
        keys = list(fast_info.keys())
    except Exception:  # pragma: no cover - defensive guard
        return snapshot

    for key in keys:
        try:
            snapshot[key] = fast_info[key]
        except Exception:
            continue
    return snapshot


def _resolve_history_window(
    period: str | None,
    start: str | None,
    end: str | None,
) -> tuple[str | None, str | None, str | None]:
    normalized_period = _normalize_optional_str(period)
    normalized_start = _normalize_optional_str(start)
    normalized_end = _normalize_optional_str(end)

    if normalized_period and (normalized_start or normalized_end):
        raise ToolError("Provide either period or start/end dates, not both.")

    if normalized_start and not normalized_end:
        raise ToolError("Provide an end date along with the start date.")

    if normalized_end and not normalized_start:
        raise ToolError("Provide a start date along with the end date.")

    if normalized_period:
        return normalized_period, None, None

    if normalized_start and normalized_end:
        return None, normalized_start, normalized_end

    return DEFAULT_PERIOD, None, None


def _validate_interval(interval: str) -> str:
    normalized = _normalize_optional_str(interval) or "1d"
    if normalized not in ALLOWED_INTERVALS:
        allowed = ", ".join(sorted(ALLOWED_INTERVALS))
        raise ToolError(f"Interval '{interval}' is not supported. Choose one of: {allowed}.")
    return normalized


def _download_history(
    ticker: str,
    *,
    period: str | None,
    start: str | None,
    end: str | None,
    interval: str,
) -> pd.DataFrame:
    ticker_obj = yf.Ticker(ticker)
    kwargs: dict[str, Any] = {"interval": interval, "auto_adjust": False}
    if period:
        kwargs["period"] = period
    else:
        kwargs["start"] = start
        kwargs["end"] = end

    frame = ticker_obj.history(**kwargs)
    return frame


def _frame_to_records(frame: pd.DataFrame) -> list[HistoryPoint]:
    records: list[HistoryPoint] = []
    for timestamp, row in frame.iterrows():
        records.append(
            HistoryPoint(
                timestamp=_timestamp_to_iso(timestamp),
                open=_clean_number(row.get("Open")),
                high=_clean_number(row.get("High")),
                low=_clean_number(row.get("Low")),
                close=_clean_number(row.get("Close")),
                adj_close=_clean_number(row.get("Adj Close")),
                volume=_clean_int(row.get("Volume")),
            )
        )
    return records


def fetch_quote(ticker: str) -> QuoteResponse:
    symbol = _normalize_ticker(ticker)
    ticker_ref = yf.Ticker(symbol)
    fast_snapshot = _extract_fast_info(ticker_ref)
    if not fast_snapshot:
        raise ToolError(f"Yahoo Finance did not return quote data for {symbol}.")

    def pick(*keys: str) -> Any:
        for key in keys:
            if key in fast_snapshot:
                value = fast_snapshot[key]
                if value is not None and not (isinstance(value, str) and not value.strip()):
                    return value
        return None

    quote: QuoteResponse = {
        "ticker": symbol,
        "timestamp": _current_timestamp(),
        "last_price": _clean_number(
            pick("last_price", "regularMarketPrice", "regularMarketPreviousClose")
        ),
        "currency": pick("currency"),
        "day_high": _clean_number(pick("day_high", "regularMarketDayHigh")),
        "day_low": _clean_number(pick("day_low", "regularMarketDayLow")),
        "open": _clean_number(pick("open", "regularMarketOpen")),
        "previous_close": _clean_number(
            pick("previous_close", "regularMarketPreviousClose")
        ),
        "volume": _clean_int(pick("last_volume", "regularMarketVolume")),
        "market_cap": _clean_number(pick("market_cap")),
    }

    if quote["last_price"] is None:
        raise ToolError(f"Quote data for {symbol} is missing price information.")

    return quote


def fetch_history(
    ticker: str,
    *,
    period: str | None = None,
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
) -> HistoryResponse:
    symbol = _normalize_ticker(ticker)
    resolved_period, resolved_start, resolved_end = _resolve_history_window(period, start, end)
    valid_interval = _validate_interval(interval)

    frame = _download_history(
        symbol,
        period=resolved_period,
        start=resolved_start,
        end=resolved_end,
        interval=valid_interval,
    )

    if frame.empty:
        raise ToolError(
            "Yahoo Finance returned no historical data for the requested window."
        )

    candles = _frame_to_records(frame)

    return {
        "ticker": symbol,
        "interval": valid_interval,
        "period": resolved_period,
        "start": resolved_start,
        "end": resolved_end,
        "candles": candles,
    }


__all__ = [
    "ALLOWED_INTERVALS",
    "DEFAULT_PERIOD",
    "HistoryPoint",
    "HistoryResponse",
    "QuoteFields",
    "QuoteResponse",
    "fetch_history",
    "fetch_quote",
]
