import time

import yfinance as yf
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

_cache: dict[str, tuple[float, float]] = {}  # ticker -> (price, fetched_at)


def _fetch_price_sync(ticker: str) -> float:
    info = yf.Ticker(ticker).fast_info
    price = info.get("last_price") if isinstance(info, dict) else getattr(info, "last_price", None)
    if price is None:
        raise ValueError(f"no price data for {ticker!r}")
    return float(price)


async def get_price(ticker: str) -> float:
    ticker = ticker.upper()
    now = time.monotonic()
    cached = _cache.get(ticker)
    if cached and now - cached[1] < settings.price_cache_ttl_seconds:
        return cached[0]

    try:
        price = await run_in_threadpool(_fetch_price_sync, ticker)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"could not fetch price for {ticker!r}: {e}") from e

    _cache[ticker] = (price, now)
    return price
