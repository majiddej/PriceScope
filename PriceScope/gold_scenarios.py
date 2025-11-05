import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.signal import find_peaks


# ---------- پارامترها ----------
SYMBOL = "GC=F"          # نماد طلا در yfinance؛ میتونی عوضش کنی (مثلاً "XAUUSD=X" یا نماد دلخواه)
PERIOD = "6mo"           # بازه زمانی برای دانلود داده (مثلاً "6mo", "1y", "3mo")
INTERVAL = "1d"          # تایم فریم: "1d", "1h", "1wk", ...
LOOKBACK_DAYS = 30       # برای یافتن سطوح حمایت/مقاومت اخیر
MA_FAST = 20
MA_SLOW = 50
ATR_PERIOD = 14

# ---------- ابزار کمکی ----------
def atr(df, n=14):
    """محاسبه ATR ساده"""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def support_resistance_levels(df, lookback=30):
    last = df.tail(lookback)
    recent_high = last['High'].max()
    recent_low = last['Low'].min()
    # سطح مقاومت دوم و حمایت دوم را با استفاده از درصد از دامنه بدست می‌آوریم
    rng = recent_high - recent_low
    resistance_2 = recent_high + 0.5 * rng
    support_2 = recent_low - 0.5 * rng
    return {
        'recent_high': recent_high,
        'recent_low': recent_low,
        'resistance_2': resistance_2,
        'support_2': support_2
    }

def market_structure(df):
    """تشخیص ساختار ساده: higher highs / lower lows در چند هفته اخیر"""
    closes = df['Close']
    # ساده‌ترین روش: مقایسه آخرین قله و دره با قبلی‌ها
    # پیدا کردن local peaks/valleys با مقایسه با همسایه‌ها



    high_vals = df['High'].to_numpy().astype(float)  # تضمین یک‌بعدی بودن
    low_vals = df['Low'].to_numpy().astype(float)

    peaks, _ = find_peaks(high_vals)
    valleys, _ = find_peaks(-low_vals)

    peak_vals = df['High'].iloc[peaks]
    valley_vals = df['Low'].iloc[valleys]


    # آخرین قله و دره
    last_peak = peak_vals.iloc[-1] if len(peak_vals) > 0 else np.nan
    prev_peak = peak_vals.iloc[-2] if len(peak_vals) > 1 else np.nan
    last_valley = valley_vals.iloc[-1] if len(valley_vals) > 0 else np.nan
    prev_valley = valley_vals.iloc[-2] if len(valley_vals) > 1 else np.nan

    structure = {}
    if not np.isnan(last_peak) and not np.isnan(prev_peak):
        structure['higher_highs'] = last_peak > prev_peak
    else:
        structure['higher_highs'] = None

    if not np.isnan(last_valley) and not np.isnan(prev_valley):
        structure['higher_lows'] = last_valley > prev_valley
    else:
        structure['higher_lows'] = None

    return structure

# ---------- هسته تحلیل ----------
def analyze_symbol(symbol=SYMBOL, period=PERIOD, interval=INTERVAL,
                   lookback_days=LOOKBACK_DAYS):
    # دانلود دیتای تاریخی
    df = yf.download(symbol, period=period, interval=interval, progress=False)

    if df.empty:
        raise RuntimeError("دیتا برای نماد مورد نظر پیدا نشد. نماد یا اتصال اینترنت را چک کن.")
    df.dropna(inplace=True)

    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    # میانگین متحرک
    df['MA_fast'] = df['Close'].rolling(MA_FAST, min_periods=1).mean()
    df['MA_slow'] = df['Close'].rolling(MA_SLOW, min_periods=1).mean()

    # ATR
    df['ATR'] = atr(df, ATR_PERIOD)

    # سطوح
    levels = support_resistance_levels(df, lookback=lookback_days)

    # ساختار بازار
    struct = market_structure(df)

    # قیمت فعلی
    last_row = df.iloc[-1]
    price = last_row['Close']
    ma_fast = last_row['MA_fast']
    ma_slow = last_row['MA_slow']
    atr_val = last_row['ATR']

    # شروط ساده برای سناریوها
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

    # ساختن سناریوها (قوانین و اهداف/ایست ضرر ساده)
    scenarios = {}

    # سناریوی صعودی
    bullish = {}
    # اگر قیمت در بالای MA50 و MA20 بالاتر از MA50 => روند صعودی
    if bullish_conditions['price_above_slow_ma'] and bullish_conditions['ma_fast_above_slow']:
        bullish['thesis'] = "روند صعودی ادامه‌دار (trend following)."
        bullish['entry_if'] = f"بازگشت به حمایت یا پولبک نزدیک {levels['recent_low']:.2f} یا شکست پایدار بالای {levels['recent_high']:.2f}."
        bullish['targets'] = [levels['recent_high'], levels['resistance_2']]
        bullish['stop_loss'] = max(levels['recent_low'] - 0.5 * atr_val, price - 2 * atr_val)  # ترکیبی از سطح حمایتی و ATR
    else:
        bullish['thesis'] = "شرایط روند صعودی قوی دیده نمی‌شود؛ در صورت شکست و تثبیت بالای مقاومت ورود کوتاه‌مدت ممکن است."
        bullish['entry_if'] = f"شکست و تثبیت بالای {levels['recent_high']:.2f}"
        bullish['targets'] = [levels['recent_high'], levels['resistance_2']]
        bullish['stop_loss'] = levels['recent_low'] - 1.0 * atr_val

    # سناریوی نزولی
    bearish = {}
    if bearish_conditions['price_below_slow_ma'] and bearish_conditions['ma_fast_below_slow']:
        bearish['thesis'] = "روند نزولی یا فشار فروش ادامه دارد."
        bearish['entry_if'] = f"شکست سطح حمایتی {levels['recent_low']:.2f} با افزایش حجم (یا کندل بسته شده زیر سطح)."
        bearish['targets'] = [levels['recent_low'], levels['support_2']]
        bearish['stop_loss'] = min(levels['recent_high'] + 0.5 * atr_val, price + 2 * atr_val)
    else:
        bearish['thesis'] = "شرایط نزولی قوی نیست؛ در صورت شکست حمایتی ورود به معامله شورت ممکن است."
        bearish['entry_if'] = f"شکست قطعی و تثبیت زیر {levels['recent_low']:.2f}"
        bearish['targets'] = [levels['recent_low'], levels['support_2']]
        bearish['stop_loss'] = levels['recent_high'] + 1.0 * atr_val

    # خلاصه وضعیت
    scenarios['symbol'] = symbol
    scenarios['date'] = df.index[-1].strftime("%Y-%m-%d %H:%M:%S")
    scenarios['price'] = price
    scenarios['ma_fast'] = ma_fast
    scenarios['ma_slow'] = ma_slow
    scenarios['atr'] = atr_val
    scenarios['levels'] = levels
    scenarios['market_structure'] = struct
    scenarios['bullish'] = bullish
    scenarios['bearish'] = bearish
    scenarios['bullish_conditions'] = bullish_conditions
    scenarios['bearish_conditions'] = bearish_conditions

    return scenarios, df

# ---------- اجرای نمونه ----------
if __name__ == "__main__":
    scn, df = analyze_symbol()
    # چاپ گزارش خلاصه
    print("=== Gold Scenarios Report ===")
    print(f"Symbol: {scn['symbol']}    Date: {scn['date']}")
    print(f"Last Price: {scn['price']:.3f}")
    print(f"MA{MA_FAST}: {scn['ma_fast']:.3f}    MA{MA_SLOW}: {scn['ma_slow']:.3f}")
    print(f"ATR({ATR_PERIOD}): {scn['atr']:.3f}")
    print("\n-- Levels --")
    for k, v in scn['levels'].items():
        print(f"{k}: {v:.3f}")
    print("\n-- Market structure --")
    print(scn['market_structure'])
    print("\n-- Bullish scenario --")
    for k, v in scn['bullish'].items():
        print(f"{k}: {v}")
    print("\nBullish conditions flags:", scn['bullish_conditions'])
    print("\n-- Bearish scenario --")
    for k, v in scn['bearish'].items():
        print(f"{k}: {v}")
    print("\nBearish conditions flags:", scn['bearish_conditions'])
