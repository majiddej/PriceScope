import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.dates import DateFormatter
from utils import get_usd_price, get_gold_18_price, calculate_gold18_bubble

# Terminal ===> streamlit run app.py



# ---------------- پارامترهای پیش‌فرض ----------------
DEFAULT_SYMBOL = "GC=F"   # اونس طلا (yfinance). می‌تونی بذاری "XAUUSD=X" یا هر نماد دیگر
DEFAULT_PERIOD = "6mo"
DEFAULT_INTERVAL = "1d"
DEFAULT_LOOKBACK = 30
MA_FAST = 20
MA_SLOW = 50
ATR_PERIOD = 14

st.set_page_config(page_title="PriceScope — Gold Scenarios", layout="wide")

# ---------------- ابزارهای کمکی ----------------
def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """اگر ستون‌ها MultiIndex هستند، آن‌ها را تخت می‌کند."""
    cols = []
    for col in df.columns:
        if isinstance(col, tuple):
            # معمولاً خروجی yfinance ممکنه ('Adj Close', '') یا ('Adj Close', 'GC=F')
            # ما سعی میکنیم اولین قسمت غیرخالی رو برداریم
            first = next((c for c in col if c not in (None, "")), col[0])
            cols.append(first)
        else:
            cols.append(col)
    df.columns = cols
    return df

def atr(df: pd.DataFrame, n:int=14) -> pd.Series:
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def support_resistance_levels(df: pd.DataFrame, lookback:int=30) -> dict:
    last = df.tail(lookback)
    recent_high = float(last['High'].max())
    recent_low = float(last['Low'].min())
    rng = recent_high - recent_low
    resistance_2 = recent_high + 0.5 * rng
    support_2 = recent_low - 0.5 * rng
    return {
        'recent_high': recent_high,
        'recent_low': recent_low,
        'resistance_2': float(resistance_2),
        'support_2': float(support_2)
    }

def market_structure(df: pd.DataFrame) -> dict:
    # تشخیص قله/کف ساده با مقایسه با همسایه‌ها (1-step local)
    peaks_mask = (df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))
    valleys_mask = (df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))
    peak_vals = df['High'][peaks_mask]
    valley_vals = df['Low'][valleys_mask]

    last_peak = float(peak_vals.iloc[-1]) if len(peak_vals) > 0 else np.nan
    prev_peak = float(peak_vals.iloc[-2]) if len(peak_vals) > 1 else np.nan
    last_valley = float(valley_vals.iloc[-1]) if len(valley_vals) > 0 else np.nan
    prev_valley = float(valley_vals.iloc[-2]) if len(valley_vals) > 1 else np.nan

    structure = {
        'higher_highs': None,
        'higher_lows': None
    }
    if not np.isnan(last_peak) and not np.isnan(prev_peak):
        structure['higher_highs'] = last_peak > prev_peak
    if not np.isnan(last_valley) and not np.isnan(prev_valley):
        structure['higher_lows'] = last_valley > prev_valley
    return structure

def to_py(v):
    """تبدیل مقادیر numpy به نوع‌های پایتونی برای نمایش"""
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, (list, tuple)):
        return [to_py(x) for x in v]
    if isinstance(v, dict):
        return {k: to_py(val) for k, val in v.items()}
    return v

# ---------------- هسته تحلیل ----------------
def analyze_symbol(symbol: str, period: str, interval: str, lookback:int):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df.empty:
        raise RuntimeError("دیتا برای نماد مورد نظر پیدا نشد. بررسی کن نماد و اتصال اینترنت را.")
    df = clean_columns(df)
    df.dropna(inplace=True)

    # محاسبات
    df['MA_fast'] = df['Close'].rolling(MA_FAST, min_periods=1).mean()
    df['MA_slow'] = df['Close'].rolling(MA_SLOW, min_periods=1).mean()
    df['ATR'] = atr(df, ATR_PERIOD)

    levels = support_resistance_levels(df, lookback)
    struct = market_structure(df)

    last = df.iloc[-1]
    price = float(last['Close'])
    ma_fast = float(last['MA_fast'])
    ma_slow = float(last['MA_slow'])
    atr_val = float(last['ATR'])

    bullish_conditions = {
        'price_above_slow_ma': price > ma_slow,
        'ma_fast_above_slow': ma_fast > ma_slow,
        'near_support': price <= levels['recent_low'] + 0.02 * (levels['recent_high'] - levels['recent_low']),
        'breakout_above_recent_high': price > levels['recent_high']
    }
    bearish_conditions = {
        'price_below_slow_ma': price < ma_slow,
        'ma_fast_below_slow': ma_fast < ma_slow,
        'near_resistance': price >= levels['recent_high'] - 0.02 * (levels['recent_high'] - levels['recent_low']),
        'breakdown_below_recent_low': price < levels['recent_low']
    }

    # سناریوها
    bullish = {}
    if bullish_conditions['price_above_slow_ma'] and bullish_conditions['ma_fast_above_slow']:
        bullish['thesis'] = "روند صعودی ادامه‌دار (trend following)."
        bullish['entry_if'] = f"پولبک یا بازگشت نزدیک {levels['recent_low']:.2f} یا شکست بالای {levels['recent_high']:.2f}."
        bullish['targets'] = [levels['recent_high'], levels['resistance_2']]
        bullish['stop_loss'] = float(max(levels['recent_low'] - 0.5 * atr_val, price - 2 * atr_val))
    else:
        bullish['thesis'] = "شرایط روند صعودی قوی نیست؛ ورود فقط پس از شکست و تثبیت مقاومت."
        bullish['entry_if'] = f"شکست و تثبیت بالای {levels['recent_high']:.2f}"
        bullish['targets'] = [levels['recent_high'], levels['resistance_2']]
        bullish['stop_loss'] = float(levels['recent_low'] - 1.0 * atr_val)

    bearish = {}
    if bearish_conditions['price_below_slow_ma'] and bearish_conditions['ma_fast_below_slow']:
        bearish['thesis'] = "روند نزولی ادامه دارد."
        bearish['entry_if'] = f"شکست حمایتی {levels['recent_low']:.2f}."
        bearish['targets'] = [levels['recent_low'], levels['support_2']]
        bearish['stop_loss'] = float(min(levels['recent_high'] + 0.5 * atr_val, price + 2 * atr_val))
    else:
        bearish['thesis'] = "شرایط نزولی قوی نیست؛ ورود شورت فقط پس از شکست حمایتی."
        bearish['entry_if'] = f"شکست و تثبیت زیر {levels['recent_low']:.2f}"
        bearish['targets'] = [levels['recent_low'], levels['support_2']]
        bearish['stop_loss'] = float(levels['recent_high'] + 1.0 * atr_val)

    scenarios = {
        'symbol': symbol,
        'date': df.index[-1].strftime("%Y-%m-%d %H:%M:%S"),
        'price': price,
        'ma_fast': ma_fast,
        'ma_slow': ma_slow,
        'atr': atr_val,
        'levels': levels,
        'market_structure': struct,
        'bullish': bullish,
        'bearish': bearish,
        'bullish_conditions': bullish_conditions,
        'bearish_conditions': bearish_conditions
    }

    # تبدیل انواع numpy به پایتون برای نمایش راحت‌تر
    scenarios = to_py(scenarios)
    return scenarios, df

# ---------------- رابط کاربری Streamlit ----------------
st.title("PriceScope — Market Scenarios Dashboard")
st.caption("تحلیل ساده سناریوی صعودی / نزولی با MA, ATR و سطوح حمایت/مقاومت")

with st.sidebar:
    st.header("Inputs")
    symbol = st.text_input("Symbol (yfinance)", DEFAULT_SYMBOL)
    period = st.selectbox("Period", ["1mo","3mo","6mo","1y","2y","5y"], index=2)
    interval = st.selectbox("Interval", ["1d","1h","4h","1wk"], index=0)
    lookback = st.number_input("Lookback days for levels", min_value=7, max_value=180, value=DEFAULT_LOOKBACK)
    run_btn = st.button("Run Analysis")

if run_btn:
    try:

        with st.spinner("Downloading data and analyzing..."):
            scenarios, df = analyze_symbol(symbol, period, interval, int(lookback))




        # --- Summary cards ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Last Price", f"{scenarios['price']:.3f}")
        col2.metric(f"MA{MA_FAST}", f"{scenarios['ma_fast']:.3f}")
        col3.metric(f"MA{MA_SLOW}", f"{scenarios['ma_slow']:.3f}")
        col4.metric(f"ATR({ATR_PERIOD})", f"{scenarios['atr']:.3f}")

        # --- levels & structure ---
        st.subheader("Support & Resistance")
        levels = scenarios['levels']
        st.write(f"Recent high: {levels['recent_high']:.2f}    Recent low: {levels['recent_low']:.2f}")
        st.write(f"Resistance2: {levels['resistance_2']:.2f}    Support2: {levels['support_2']:.2f}")

        st.subheader("Market Structure & Conditions")
        st.json({
            "market_structure": scenarios['market_structure'],
            "bullish_conditions": scenarios['bullish_conditions'],
            "bearish_conditions": scenarios['bearish_conditions']
        })

        # --- Scenarios human-friendly ---
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
        # سطوح
        ax.axhline(levels['recent_high'], linestyle='--', label='Recent High')
        ax.axhline(levels['recent_low'], linestyle='--', label='Recent Low')
        ax.axhline(levels['resistance_2'], linestyle=':', label='Resistance2')
        ax.axhline(levels['support_2'], linestyle=':', label='Support2')

        ax.set_title(f"{symbol} — Close + MAs")
        ax.legend()
        ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        st.pyplot(fig)

                # ===== قیمت‌های بازار ایران =====
        usd_price = get_usd_price()               # تومان
        gold18_market = get_gold_18_price()       # تومان
        ounce_price = scenarios['price']          # قیمت جهانی اونس از yfinance

        bubble_data = calculate_gold18_bubble(
        ounce_price_usd=ounce_price,
        usd_price_toman=usd_price,
        gold18_market_toman=gold18_market
        )

        st.write(f"💵 دلار آزاد: **{usd_price:,}** تومان")
        st.write(f"🥇 قیمت بازار طلای ۱۸: **{gold18_market:,}** تومان")
        st.write(f"🌍 قیمت جهانی معادل هر گرم طلای ۱۸: **{bubble_data['gold18_global_toman']:,}** تومان")
        st.write(f"🎈 مقدار حباب: **{bubble_data['bubble_toman']:,}** تومان")

        # --- Raw data (optional) ---
        if st.checkbox("Show raw OHLC data"):
            st.dataframe(df.tail(200))

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("برای شروع آنالیز، از سمت چپ پارامترها را تغییر بده و روی 'Run Analysis' کلیک کن.")
