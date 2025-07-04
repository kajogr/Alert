import requests
import pandas as pd
from datetime import datetime
import os

PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

# CoinGecko ids (όχι symbols!)
coins = {
    "SOL": "solana",
    "IOTX": "iotex",
    "SUI": "sui",
    "ETH": "ethereum",
    "PEPE": "pepe",
    "SAGA": "saga"
}

def get_prices(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    res = requests.get(url, params=params).json()
    prices = [p[1] for p in res.get("prices", [])]
    if not prices:
        print(f"⚠️ API ERROR for {coin_id}: {res}")
    return prices

def calc_rsi(prices, period=14):
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calc_ma(prices, period=20):
    ma = pd.Series(prices).rolling(window=period).mean()
    return ma.iloc[-1]

def calc_macd(prices):
    prices = pd.Series(prices)
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line.iloc[-1], signal.iloc[-1]

def send_push(message):
    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message
        }
    )
    print(f"🔔 Push Response: {response.text}")

def main():
    sent = False
    for symbol, coin_id in coins.items():
        prices = get_prices(coin_id)
        if not prices:
            print(f"⏭️ No data for {symbol}, skipping...")
            continue

        last = prices[-1]
        rsi = calc_rsi(prices)
        ma = calc_ma(prices)
        macd, signal = calc_macd(prices)

        alert = []
        if rsi < 30:
            alert.append("RSI κάτω από 30 (υπερπώληση)")
        elif rsi > 70:
            alert.append("RSI πάνω από 70 (υπεραγορά)")

        if macd > signal:
            alert.append("MACD bullish crossover")
        elif macd < signal:
            alert.append("MACD bearish crossover")

        if last > ma:
            alert.append("Τιμή πάνω από MA20 (breakout)")
        elif last < ma:
            alert.append("Τιμή κάτω από MA20 (breakdown)")

        msg = f"{symbol} (${last:.4f})\n" + "\n".join(alert if alert else ["🚨 No strong signal"])
        send_push(msg)
        sent = True

    if not sent:
        send_push("🚨 TEST ALERT: No valid data but push works!")

if __name__ == "__main__":
    print(f"🔔 Crypto Alerts @ {datetime.now()}")
    main()
