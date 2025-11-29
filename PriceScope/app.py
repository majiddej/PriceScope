import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from config import *
from analysis.data_fetcher import fetch_data
from analysis.indicators import atr, moving_averages, support_resistance_levels, market_structure
from analysis.scenarios import generate_scenarios

st.set_page_config(page_title="PriceScope — Gold Dashboard", layout="wide")
st.title("PriceScope — Market Scenarios Dashboard")

# --- Sidebar ---
with st.sidebar:
    st.header("Inputs")
    symbol = st.text_input("Symbol (yfinance)", DEFAULT_SYMBOL)
    period = st.selectbox("Period", ["1mo","3mo","6mo","1y","2y","5y"], index=2)
    interval = st.selectbox("Interval", ["1d","1h","4h","1wk"], index=0)
    lookback = st.number_input("Lookback days for levels", min_value=7, max_value=180, value=DEFAULT_LOOKBACK)
    run_btn = st.button("Run Analysis")

# --- Run Analysis ---
if run_btn:
    df = fetch_data(symbol, period, interval)
    df = moving_averages(df, MA_FAST, MA_SLOW)
    df['ATR'] = atr(df, ATR_PERIOD)
    levels = support_resistance_levels(df, lookback)
    struct = market_structure(df)
    scenarios = generate_scenarios(df, levels, struct)

    # --- Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Last Price", f"{scenarios['price']:.3f}")
    col2.metric(f"MA{MA_FAST}", f"{scenarios['ma_fast']:.3f}")
    col3.metric(f"MA{MA_SLOW}", f"{scenarios['ma_slow']:.3f}")
    col4.metric(f"ATR({ATR_PERIOD})", f"{scenarios['atr']:.3f}")

    # --- Levels & Structure ---
    st.subheader("Support & Resistance")
    st.write(f"Recent High: {levels['recent_high']:.2f}, Recent Low: {levels['recent_low']:.2f}")
    st.write(f"Resistance2: {levels['resistance_2']:.2f}, Support2: {levels['support_2']:.2f}")
    st.subheader("Market Structure & Conditions")
    st.json({
        "market_structure": scenarios['market_structure'],
        "bullish_conditions": scenarios['bullish_conditions'],
        "bearish_conditions": scenarios['bearish_conditions']
    })

    # --- Scenarios ---
    st.subheader("Scenarios")
    st.markdown("**Bullish (صعودی)**")
    st.write(f"Thesis: {scenarios['bullish']['thesis']}")
    st.write(f"Entry if: {scenarios['bullish']['entry_if']}")
    st.write(f"Targets: {scenarios['bullish']['targets']}")
    st.write(f"Stop loss: {scenarios['bullish']['stop_loss']:.2f}")

    st.markdown("**Bearish (نزولی)**")
    st.write(f"Thesis: {scenarios['bearish']['thesis']}")
    st.write(f"Entry if: {scenarios['bearish']['entry_if']}")
    st.write(f"Targets: {scenarios['bearish']['targets']}")
    st.write(f"Stop loss: {scenarios['bearish']['stop_loss']:.2f}")

    # --- Chart ---
    st.subheader("Price Chart")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df['Close'], label='Close')
    ax.plot(df.index, df['MA_fast'], label=f"MA{MA_FAST}")
    ax.plot(df.index, df['MA_slow'], label=f"MA{MA_SLOW}")
    ax.axhline(levels['recent_high'], linestyle='--', label='Recent High')
    ax.axhline(levels['recent_low'], linestyle='--', label='Recent Low')
    ax.axhline(levels['resistance_2'], linestyle=':', label='Resistance2')
    ax.axhline(levels['support_2'], linestyle=':', label='Support2')
    ax.set_title(f"{symbol} — Close + MAs")
    ax.legend()
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    st.pyplot(fig)

else:
    st.info("برای شروع آنالیز، پارامترها را در سایدبار تنظیم کرده و روی 'Run Analysis' کلیک کنید.")
