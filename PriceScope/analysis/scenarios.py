# analysis/scenarios.py
import numpy as np

def to_py(v):
    """تبدیل numpy types به پایتون برای نمایش"""
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, (list, tuple)):
        return [to_py(x) for x in v]
    if isinstance(v, dict):
        return {k: to_py(val) for k, val in v.items()}
    return v

def generate_scenarios(df, levels, struct, ma_fast_col='MA_fast', ma_slow_col='MA_slow', atr_col='ATR'):
    last = df.iloc[-1]
    price = float(last['Close'])
    ma_fast = float(last[ma_fast_col])
    ma_slow = float(last[ma_slow_col])
    atr_val = float(last[atr_col])

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

    # سناریوی صعودی
    if bullish_conditions['price_above_slow_ma'] and bullish_conditions['ma_fast_above_slow']:
        bullish = {
            'thesis': "روند صعودی ادامه‌دار (trend following).",
            'entry_if': f"پولبک یا بازگشت نزدیک {levels['recent_low']:.2f} یا شکست بالای {levels['recent_high']:.2f}.",
            'targets': [levels['recent_high'], levels['resistance_2']],
            'stop_loss': float(max(levels['recent_low'] - 0.5 * atr_val, price - 2*atr_val))
        }
    else:
        bullish = {
            'thesis': "شرایط روند صعودی قوی نیست؛ ورود فقط پس از شکست و تثبیت مقاومت.",
            'entry_if': f"شکست و تثبیت بالای {levels['recent_high']:.2f}",
            'targets': [levels['recent_high'], levels['resistance_2']],
            'stop_loss': float(levels['recent_low'] - 1.0*atr_val)
        }

    # سناریوی نزولی
    if bearish_conditions['price_below_slow_ma'] and bearish_conditions['ma_fast_below_slow']:
        bearish = {
            'thesis': "روند نزولی ادامه دارد.",
            'entry_if': f"شکست حمایتی {levels['recent_low']:.2f}.",
            'targets': [levels['recent_low'], levels['support_2']],
            'stop_loss': float(min(levels['recent_high'] + 0.5*atr_val, price + 2*atr_val))
        }
    else:
        bearish = {
            'thesis': "شرایط نزولی قوی نیست؛ ورود شورت فقط پس از شکست حمایتی.",
            'entry_if': f"شکست و تثبیت زیر {levels['recent_low']:.2f}",
            'targets': [levels['recent_low'], levels['support_2']],
            'stop_loss': float(levels['recent_high'] + 1.0*atr_val)
        }

    scenarios = {
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

    return to_py(scenarios)
