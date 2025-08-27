from datetime import datetime
from sqlmodel import SQLModel
from sqlalchemy import PrimaryKeyConstraint


class StockDailyPrice(SQLModel, table=True):
    ticker: str
    date: datetime
    adj_close: float
    close: float
    high: float
    low: float
    open: float
    volume: int

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "date"),
    )
