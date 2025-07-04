import requests
import pandas as pd
from datetime import datetime
import os

# Pushover secrets
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

# CoinGecko ids
coins = {
    "SOL": "solana",
    "IOTX": "iotex",
    "SUI": "sui",
    "ETH": "ethereum",
    "PEPE": "pepe",
    "SAGA": "saga"
}

# Παίρνει ιστορικά daily prices
def get_prices(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    res = requests.get(url, params=params).json()
    prices = [p[1] for p in res.get("prices", [])]
    if not prices:
        print(f"⚠️ API ERROR for {coin_id}: {res}")
    return prices

# RSI
def calc_rsi(prices, period=14):
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# MA20
def calc_ma(prices, period=20):
    ma = pd.Series(prices).rolling(window=period).mean()
    return ma.iloc[-1]

# MACD
def calc_macd(prices):
    prices = pd.Series(prices)
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line.iloc[-1], signal.iloc[-1]

# Στέλνει push
def send_push(message):
    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message
        }
    )
    print(f"🔔 Push Response: {response.status_code} | {response.text}")

# ΟΛΗ η λογική
def main():
    print(f"🔔 Crypto Alerts @ {datetime.now()}")
    sent = False

    entry_prices = {}

    for symbol, coin_id in coins.items():
        print(f"\n🔎 Checking {symbol} ({coin_id})")
        prices = get_prices(coin_id)
        print(f"Prices: last 5 → {prices[-5:]}")

        if not prices:
            print(f"⏭️ No data for {symbol}, skipping...")
            continue

        last = prices[-1]

        # Αν δεν υπάρχει entry price ➜ θέτουμε το τρέχον
        if symbol not in entry_prices:
            entry_prices[symbol] = last

        entry = entry_prices[symbol]
        change_pct = ((last - entry) / entry) *
