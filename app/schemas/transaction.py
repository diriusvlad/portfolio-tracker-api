from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    type: TransactionType
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    fee: float = Field(ge=0, default=0)
    executed_at: datetime


class TransactionRead(BaseModel):
    id: int
    ticker: str
    type: TransactionType
    quantity: float
    price: float
    fee: float
    executed_at: datetime

    model_config = {"from_attributes": True}
