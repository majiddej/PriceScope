import requests
from bs4 import BeautifulSoup

# ---------------- TLS / SSL Fix ----------------
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


# ---------------- خواندن قیمت از TGJU ----------------
def _scrape_tgju_item(code: str) -> int:
    """
    دریافت قیمت از سایت tgju.org
    مثال‌ها:
    دلار: price_dollar_rl
    طلای 18: geram18
    """
    url = f"https://www.tgju.org/profile/{code}"

    try:
        r = requests.get(url, headers=headers, timeout=8)
        r.raise_for_status()
    except:
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    price_tag = soup.select_one("span.info__price") or soup.select_one("#info-price")
    if not price_tag:
        return None

    price_text = price_tag.text.replace(",", "").strip()

    try:
        return int(float(price_text))
    except:
        return None


# ---------------- قیمت دلار بازار آزاد ----------------
def get_usd_price() -> int:
    # کد دلار آزاد در tgju
    price = _scrape_tgju_item("price_dollar_rl")
    if price:
        return price

    # fallback (API)
    try:
        r = requests.get("https://api.tgju.online/v1/data/detail/price_dollar_rl", timeout=8)
        j = r.json()
        return int(j["data"]["p"])
    except:
        return 0


# ---------------- قیمت طلای 18 عیار ----------------
def get_gold_18_price() -> int:
    price = _scrape_tgju_item("geram18")
    if price:
        return price

    # fallback
    try:
        r = requests.get("https://api.tgju.online/v1/data/detail/geram18", timeout=8)
        j = r.json()
        return int(j["data"]["p"])
    except:
        return 0


# ---------------- محاسبه حباب گرم طلا ----------------
def calculate_gold18_bubble(usd_price: int, gold_18_price: int) -> int:
    """
    فرمول مرجع محاسبه ارزش ذاتی گرم:
        ارزش ذاتی = (اونس * دلار * 0.0116) * (عیار / 24)
    که برای 18 عیار می‌شود * 0.75
    """
    # قیمت اونس جهانی به دلار از yfinance داخل app گرفته می‌شود
    # اینجا فقط ریال محاسبه می‌کنیم

    OUNCE_USD = 1  # مقدار واقعی در app.py محاسبه می‌شود، اینجا bubble بر اساس بازار داخلی است

    intrinsic = usd_price * 0.0116 * 0.75 * OUNCE_USD
    bubble = gold_18_price - intrinsic

    return int(bubble)
