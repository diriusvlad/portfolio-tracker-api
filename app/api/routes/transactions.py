from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.routes.portfolios import _get_owned_portfolio
from app.db.models.asset import Asset
from app.db.models.transaction import Transaction
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.transaction import TransactionCreate, TransactionRead

router = APIRouter(prefix="/portfolios/{portfolio_id}/transactions", tags=["transactions"])


async def _get_or_create_asset(ticker: str, db: AsyncSession) -> Asset:
    ticker = ticker.upper()
    asset = await db.scalar(select(Asset).where(Asset.ticker == ticker))
    if asset is None:
        asset = Asset(ticker=ticker)
        db.add(asset)
        await db.flush()
    return asset


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    portfolio_id: int,
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionRead:
    await _get_owned_portfolio(portfolio_id, current_user, db)
    asset = await _get_or_create_asset(payload.ticker, db)

    transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        type=payload.type,
        quantity=payload.quantity,
        price=payload.price,
        fee=payload.fee,
        executed_at=payload.executed_at,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    return TransactionRead(
        id=transaction.id,
        ticker=asset.ticker,
        type=transaction.type,
        quantity=float(transaction.quantity),
        price=float(transaction.price),
        fee=float(transaction.fee),
        executed_at=transaction.executed_at,
    )


@router.get("", response_model=list[TransactionRead])
async def list_transactions(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TransactionRead]:
    await _get_owned_portfolio(portfolio_id, current_user, db)
    result = await db.execute(
        select(Transaction)
        .where(Transaction.portfolio_id == portfolio_id)
        .options(selectinload(Transaction.asset))
        .order_by(Transaction.executed_at)
    )
    transactions = result.scalars().all()
    return [
        TransactionRead(
            id=t.id,
            ticker=t.asset.ticker,
            type=t.type,
            quantity=float(t.quantity),
            price=float(t.price),
            fee=float(t.fee),
            executed_at=t.executed_at,
        )
        for t in transactions
    ]
