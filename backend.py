import os
import json
import pandas as pd
import yfinance as yf
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from sqlmodel import Session, select

from db import engine, create_db_and_tables
from models import StockDailyPrice, StockTranscript, StockTranscriptSummary

load_dotenv()

from transcript import TICKER_MAPPING, get_transcript_path, load_transcript, preprocess_transcript
from transcript import extract_summary, extract_revenue_profit_highlights, extract_management_commentary, extract_guidance_outlook, extract_qna_key_points

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def read_root():
    return {"status": "ok"}


def _parse_df(df: pd.DataFrame) -> List[dict]:
    records = df.to_json(orient="records")
    parsed = json.loads(records)
    return parsed


@app.get("/search/yfin")
def search_yfin(
    query: str = Query("HDFC", description="Search query for stock ticker"),
    limit: int = Query(25, ge=1, le=250, description="Maximum number of results"),
):
    yf_lookup = yf.Lookup(query)
    stocks_df = yf_lookup.get_stock(count=limit).reset_index()
    parsed = _parse_df(stocks_df)
    
    return {
        "count": len(parsed),
        "tickers": [row["symbol"] for row in parsed],
        "data": parsed,
    }


def get_nifty_500_stocks():
    df = pd.read_csv("MW-NIFTY-500-27-Aug-2025.csv")
    stock_list = df.iloc[1:]['SYMBOL \n'].values.tolist()
    return stock_list


@app.get("/search", response_model=list[str])
def search(
    query: str = Query("HDFC", description="Search query for stock ticker in NIFTY 500 NSE"),
):
    stock_list = get_nifty_500_stocks()
    filtered_stock_list = [f"{s}.NS" for s in stock_list if query.lower() in s.lower()]
    return filtered_stock_list


@app.get("/fetch", response_model=list[StockDailyPrice])
def get_history(
    ticker: str = Query("HDFCBANK.NS", description="Stock ticker"),
    period: str = Query("3y", description="yfinance period (e.g., 3y)"),
    interval: str = Query("1d", description="yfinance interval (e.g., 1d, 1wk)"),
):
    ticker = ticker.strip().upper()

    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False, threads=True)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Failed to fetch data from upstream: {exc}")

    history_df = df.reset_index()
    history_df.columns = [col[0] for col in history_df.columns]


    with Session(engine) as session:
        sdp_list = [
            StockDailyPrice(
                ticker=ticker,
                date=row["Date"],
                adj_close=row["Adj Close"],
                close=row["Close"],
                high=row["High"],
                low=row["Low"],
                open=row["Open"],
                volume=row["Volume"]
            )
            for _, row in history_df.iterrows()
        ]

        existing_sdp_list = session.exec(select(StockDailyPrice).where(StockDailyPrice.ticker == ticker)).all()
        existing_date_list = [pd.to_datetime(sdp.date) for sdp in existing_sdp_list]

        new_sdp_list = [sdp for sdp in sdp_list if pd.to_datetime(sdp.date) not in existing_date_list]
        session.add_all(new_sdp_list)
        session.commit()

        [session.refresh(sdp) for sdp in new_sdp_list]

    return sdp_list


@app.get("/transcript/all", response_model=list[str])
def get_transcript_list(
    ticker: str = Query("HDFCBANK.NS", description="Stock ticker"),
):
    if ticker not in TICKER_MAPPING:
        return []
    
    file_ticker = TICKER_MAPPING[ticker]
    quarters = [fname[:-4].split('_')[1] for fname in os.listdir('./pdfs/') if ('.pdf' in fname.lower()) and (file_ticker.lower() in fname.lower())]
    return quarters


@app.get("/transcript", response_model=list[StockTranscript])
def get_transcript(
    ticker: str = Query("HDFCBANK.NS", description="Stock ticker"),
    quarter: str = Query("2025Q1", description="Quarter for which to fetch the call transcript summary")
):
    ticker = ticker.strip().upper()

    with Session(engine) as session:
        stock_transcript_list = session.exec(select(StockTranscript).where(StockTranscript.ticker == ticker, StockTranscript.quarter == quarter)).all()
        
        if len(stock_transcript_list) == 0:
            filepath = get_transcript_path(ticker, quarter)
            reader = load_transcript(filepath)
            transcript_df = preprocess_transcript(reader)
            stock_transcript_list = [
                StockTranscript(
                    ticker=ticker,
                    quarter=quarter,
                    transcript_index=row["transcript_index"],
                    speaker=row["speaker"],
                    speaker_type=row["speaker_type"],
                    transcript=row["transcript"],
                )
                for _, row in transcript_df.iterrows()
            ]

            session.add_all(stock_transcript_list)
            session.commit()

            [session.refresh(st) for st in stock_transcript_list]

    return stock_transcript_list


@app.get("/summary", response_model=StockTranscriptSummary)
def get_summary(
    ticker: str = Query("HDFCBANK.NS", description="Stock ticker"),
    quarter: str = Query("2025Q1", description="Quarter for which to fetch the call transcript summary")
):
    ticker = ticker.strip().upper()

    with Session(engine) as session:
        stock_transcript_summary = session.exec(select(StockTranscriptSummary).where(StockTranscriptSummary.ticker == ticker, StockTranscriptSummary.quarter == quarter)).first()
        
        if not stock_transcript_summary:
            stock_transcript_list = get_transcript(ticker, quarter)
            transcript_df = pd.DataFrame([st.model_dump() for st in stock_transcript_list])
            print(transcript_df)

            summary = extract_summary(transcript_df)
            revenue_profit_highlight_dict = extract_revenue_profit_highlights(transcript_df)
            management_commentary = extract_management_commentary(transcript_df)
            guidance_outlook_summary_dict = extract_guidance_outlook(transcript_df)
            qna_key_points = extract_qna_key_points(transcript_df)

            stock_transcript_summary = StockTranscriptSummary(
                ticker=ticker,
                quarter=quarter,
                summary=summary,
                revenue_profit_highlight_management=revenue_profit_highlight_dict['management'],
                revenue_profit_highlight_qna=revenue_profit_highlight_dict['qna'],
                management_commentary=management_commentary,
                guidance_outlook_summary_management=guidance_outlook_summary_dict['management'],
                guidance_outlook_summary_qna=guidance_outlook_summary_dict['qna'],
                qna_key_points=qna_key_points
            )

            session.add(stock_transcript_summary)
            session.commit()
            
            session.refresh(stock_transcript_summary)

    return stock_transcript_summary
