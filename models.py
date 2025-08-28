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


class StockTranscript(SQLModel, table=True):
    ticker: str
    quarter: str
    transcript_index: int
    speaker: str
    speaker_type: str
    transcript: str

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "quarter", "transcript_index"),
    )


class StockTranscriptSummary(SQLModel, table=True):
    ticker: str
    quarter: str
    summary: str
    revenue_profit_highlight_management: str
    revenue_profit_highlight_qna: str
    management_commentary: str
    guidance_outlook_summary_management: str
    guidance_outlook_summary_qna: str
    qna_key_points: str

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "quarter"),
    )
