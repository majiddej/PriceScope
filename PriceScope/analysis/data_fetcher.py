# analysis/data_fetcher.py
import yfinance as yf
import pandas as pd

def fetch_data(symbol, period="6mo", interval="1d"):
    """دانلود دیتا از yfinance و اصلاح MultiIndex"""
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    df.dropna(inplace=True)
    # اصلاح ستون‌ها اگر MultiIndex هستند
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    return df
