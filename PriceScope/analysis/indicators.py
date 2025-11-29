# analysis/indicators.py
import pandas as pd
import numpy as np

def atr(df: pd.DataFrame, n:int=14) -> pd.Series:
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def moving_averages(df: pd.DataFrame, fast=20, slow=50):
    df['MA_fast'] = df['Close'].rolling(fast, min_periods=1).mean()
    df['MA_slow'] = df['Close'].rolling(slow, min_periods=1).mean()
    return df

def support_resistance_levels(df: pd.DataFrame, lookback:int=30) -> dict:
    last = df.tail(lookback)
    recent_high = float(last['High'].max())
    recent_low = float(last['Low'].min())
    rng = recent_high - recent_low
    return {
        'recent_high': recent_high,
        'recent_low': recent_low,
        'resistance_2': recent_high + 0.5*rng,
        'support_2': recent_low - 0.5*rng
    }

def market_structure(df: pd.DataFrame) -> dict:
    peaks = (df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))
    valleys = (df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))
    peak_vals = df['High'][peaks]
    valley_vals = df['Low'][valleys]
    last_peak = float(peak_vals.iloc[-1]) if len(peak_vals) > 0 else np.nan
    prev_peak = float(peak_vals.iloc[-2]) if len(peak_vals) > 1 else np.nan
    last_valley = float(valley_vals.iloc[-1]) if len(valley_vals) > 0 else np.nan
    prev_valley = float(valley_vals.iloc[-2]) if len(valley_vals) > 1 else np.nan
    return {
        'higher_highs': None if np.isnan(last_peak) or np.isnan(prev_peak) else last_peak > prev_peak,
        'higher_lows': None if np.isnan(last_valley) or np.isnan(prev_valley) else last_valley > prev_valley
    }
