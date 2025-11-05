import requests

def get_gold_ounce_price_usd(api_key):
    price_usd = 4000
    return price_usd


    # # مثال برای Metals-API
    # url = f"https://api.metals-api.com/v1/latest?access_key={api_key}&symbols=XAU&base=USD"
    # resp = requests.get(url)
    # resp.raise_for_status()
    # data = resp.json()
    # # برگردان قیمت اونس طلا (XAU) به دلار
    # # توجه: ممکنه نتیجه به “1 XAU = … USD” باشه یا برعکس
    # price_usd = data["rates"]["XAU"]
    # return price_usd

def get_usd_to_irr_rate(api_key):
    rate = 108400
    return rate
    # # مثال برای CurrencyAPI
    # url = f"https://api.currencyapi.com/v3/latest?apikey={api_key}&base=USD&symbols=IRR"
    # resp = requests.get(url)
    # resp.raise_for_status()
    # data = resp.json()
    # rate = data["data"]["IRR"]["value"]
    # return rate

def calculate_gold_bubble(ounce_price_usd, usd_to_irr, market_price_per_gram_toman):
    OUNCE_TO_GRAM = 31.103431
    PURITY_18K = 0.75

    # قیمت ذاتی هر گرم طلا ۱۸ عیار
    intrinsic_price_toman = (ounce_price_usd / OUNCE_TO_GRAM) * PURITY_18K * usd_to_irr

    bubble_toman = market_price_per_gram_toman - intrinsic_price_toman

    return intrinsic_price_toman, bubble_toman

if __name__ == "__main__":
    gold_api_key = "YOUR_METALS_API_KEY"
    fx_api_key   = "YOUR_CURRENCY_API_KEY"
    market_price = 10558600  # مثال: قیمت بازار هر گرم ۱۸ عیار به تومان

    ounce_usd    = get_gold_ounce_price_usd(gold_api_key)
    usd_to_irr   = get_usd_to_irr_rate(fx_api_key)

    intrinsic, bubble = calculate_gold_bubble(ounce_usd, usd_to_irr, market_price)

    print(f"قیمت ذاتی هر گرم طلا ۱۸ عیار: {intrinsic:,.0f} تومان")
    print(f"مقدار حباب: {bubble:,.0f} تومان")
