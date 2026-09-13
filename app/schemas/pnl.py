from pydantic import BaseModel


class HoldingPnL(BaseModel):
    ticker: str
    quantity: float
    avg_cost: float
    current_price: float | None
    market_value: float | None
    unrealized_pnl: float | None
    realized_pnl: float


class PortfolioPnL(BaseModel):
    portfolio_id: int
    holdings: list[HoldingPnL]
    total_market_value: float
    total_unrealized_pnl: float
    total_realized_pnl: float
