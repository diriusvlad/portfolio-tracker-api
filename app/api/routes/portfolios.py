from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.portfolio import Portfolio
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.pnl import PortfolioPnL
from app.schemas.portfolio import PortfolioCreate, PortfolioRead
from app.services.pnl_service import compute_portfolio_pnl

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


async def _get_owned_portfolio(portfolio_id: int, current_user: User, db: AsyncSession) -> Portfolio:
    portfolio = await db.get(Portfolio, portfolio_id)
    if portfolio is None or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="portfolio not found")
    return portfolio


@router.post("", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Portfolio:
    portfolio = Portfolio(name=payload.name, user_id=current_user.id)
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)
    return portfolio


@router.get("", response_model=list[PortfolioRead])
async def list_portfolios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Portfolio]:
    result = await db.execute(select(Portfolio).where(Portfolio.user_id == current_user.id))
    return list(result.scalars().all())


@router.get("/{portfolio_id}", response_model=PortfolioRead)
async def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Portfolio:
    return await _get_owned_portfolio(portfolio_id, current_user, db)


@router.get("/{portfolio_id}/pnl", response_model=PortfolioPnL)
async def get_portfolio_pnl(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortfolioPnL:
    await _get_owned_portfolio(portfolio_id, current_user, db)
    return await compute_portfolio_pnl(db, portfolio_id)
