import asyncio
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.transaction import Transaction, TransactionType
from app.schemas.pnl import HoldingPnL, PortfolioPnL
from app.services.price_service import get_price


@dataclass
class _Position:
    quantity: float = 0.0
    cost_basis: float = 0.0
    realized_pnl: float = 0.0

    @property
    def avg_cost(self) -> float:
        return self.cost_basis / self.quantity if self.quantity > 1e-12 else 0.0


def _apply_average_cost(transactions: list[Transaction]) -> _Position:
    """Weighted-average-cost method: each sell realizes P&L against the
    running average cost of shares held at that point, then shrinks the
    cost basis proportionally."""
    pos = _Position()
    for t in sorted(transactions, key=lambda t: t.executed_at):
        qty, price, fee = float(t.quantity), float(t.price), float(t.fee)
        if t.type == TransactionType.BUY:
            pos.cost_basis += qty * price + fee
            pos.quantity += qty
        else:
            avg_cost = pos.avg_cost
            pos.realized_pnl += (price - avg_cost) * qty - fee
            pos.cost_basis -= avg_cost * qty
            pos.quantity -= qty
    return pos


async def compute_portfolio_pnl(db: AsyncSession, portfolio_id: int) -> PortfolioPnL:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.portfolio_id == portfolio_id)
        .options(selectinload(Transaction.asset))
    )
    transactions = result.scalars().all()

    by_ticker: dict[str, list[Transaction]] = defaultdict(list)
    for t in transactions:
        by_ticker[t.asset.ticker].append(t)

    positions = {ticker: _apply_average_cost(txs) for ticker, txs in by_ticker.items()}

    priced_tickers = [ticker for ticker, pos in positions.items() if pos.quantity > 1e-9]
    prices = await asyncio.gather(*(get_price(t) for t in priced_tickers), return_exceptions=True)
    price_by_ticker = {
        ticker: (p if not isinstance(p, Exception) else None) for ticker, p in zip(priced_tickers, prices)
    }

    holdings: list[HoldingPnL] = []
    total_market_value = 0.0
    total_unrealized = 0.0
    total_realized = 0.0

    for ticker, pos in sorted(positions.items()):
        current_price = price_by_ticker.get(ticker)
        market_value = current_price * pos.quantity if current_price is not None and pos.quantity > 1e-9 else None
        unrealized = (current_price - pos.avg_cost) * pos.quantity if market_value is not None else None

        holdings.append(HoldingPnL(
            ticker=ticker,
            quantity=pos.quantity,
            avg_cost=pos.avg_cost,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=unrealized,
            realized_pnl=pos.realized_pnl,
        ))
        total_market_value += market_value or 0.0
        total_unrealized += unrealized or 0.0
        total_realized += pos.realized_pnl

    return PortfolioPnL(
        portfolio_id=portfolio_id,
        holdings=holdings,
        total_market_value=total_market_value,
        total_unrealized_pnl=total_unrealized,
        total_realized_pnl=total_realized,
    )
