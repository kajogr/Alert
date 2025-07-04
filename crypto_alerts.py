import requests
import pandas as pd
from datetime import datetime
import os

PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

symbols = ["SOLUSDT", "IOTXUSDT", "SUIUSDT", "ETHUSDT", "PEPEUSDT", "SAGAUSDT", "USDCUSDT"]

def get_klines(symbol, interval="1h", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    res = requests.get(url, params=params).json()
    if isinstance(res, dict) and 'code' in res:
        print(f"⚠️ API ERROR for {symbol}: {res}")
        return []
    closes = [float(k[4]) for k in res]
    return closes

def calc_rsi(prices, period=14):
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calc_ma(prices, period=50):
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
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message
        }
    )

def main():
    for symbol in symbols:
        prices = get_klines(symbol)
        if not prices:
            print(f"⏭️ No data for {symbol}, skipping...")
            continue

        last = prices[-1]
        rsi = calc_rsi(prices)
        ma50 = calc_ma(prices)
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

        if last > ma50:
            alert.append("Τιμή πάνω από MA50 (breakout)")
        elif last < ma50:
            alert.append("Τιμή κάτω από MA50 (breakdown)")

        msg = f"{symbol}\nΤιμή: {last:.4f}\n" + "\n".join(alert if alert else ["🚨 Test Alert!"])
        send_push(msg)

if __name__ == "__main__":
    print(f"🔔 Crypto Alerts @ {datetime.now()}")
    main()
