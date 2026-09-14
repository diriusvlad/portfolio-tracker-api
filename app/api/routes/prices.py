from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.services.price_service import get_price

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/{ticker}")
async def read_price(ticker: str, current_user: User = Depends(get_current_user)) -> dict:
    price = await get_price(ticker)
    return {"ticker": ticker.upper(), "price": price}
