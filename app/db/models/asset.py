from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False, default="stock")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="asset")
