import requests
import pandas as pd
from datetime import datetime
import os

# Pushover secrets από GitHub Secrets
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

# Τα coins
coins = {
    "SOL": "solana",
    "IOTX": "iotex",
    "SUI": "sui",
    "ETH": "ethereum",
    "PEPE": "pepe",
    "SAGA": "saga"
}

# Entry prices — ΣΤΑΘΕΡΑ μέσα στο script
entry_prices = {
    "SOL": 150.00,
    "IOTX": 0.021,
    "SUI": 2.92,
    "ETH": 2550.00,
    "PEPE": 0.00000097,
    "SAGA": 0.21  # ✅ ΟΚ όπως το θες!
}

def get_prices(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    res = requests.get(url, params=params).json()
    prices = [p[1] for p in res.get("prices", [])]
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
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message
        }
    )

def main():
    print(f"🔔 Crypto Alerts @ {datetime.now()}")

    for symbol, coin_id in coins.items():
        prices = get_prices(coin_id)
        if not prices:
            continue

        last = prices[-1]
        entry = entry_prices.get(symbol, last)
        change_pct = ((last - entry) / entry) * 100 if entry > 0 else 0

        rsi = calc_rsi(prices)
        ma = calc_ma(prices)
        macd, signal = calc_macd(prices)

        alert = []
        recommendation = "ΑΝΑΜΟΝΗ"

        if rsi < 30:
            alert.append("RSI κάτω από 30 ➜ Υπερπώληση")
            recommendation = "ΑΓΟΡΑ"
        elif rsi > 70:
            alert.append("RSI πάνω από 70 ➜ Υπεραγορά")
            recommendation = "ΟΧΙ ΑΓΟΡΑ"

        if macd > signal:
            alert.append("MACD bullish crossover")
            recommendation = "ΑΓΟΡΑ"
        elif macd < signal:
            alert.append("MACD bearish crossover")
            recommendation = "ΟΧΙ ΑΓΟΡΑ"

        if last > ma:
            alert.append("Τιμή πάνω από MA20 ➜ Breakout")
            recommendation = "ΑΓΟΡΑ"
        elif last < ma:
            alert.append("Τιμή κάτω από MA20 ➜ Breakdown")
            recommendation = "ΟΧΙ ΑΓΟΡΑ"

        if change_pct >= 100:
            alert.append(f"Τιμή +{change_pct:.2f}% ➜ ΟΛΙΚΗ ΠΩΛΗΣΗ")
            recommendation = "ΠΩΛΗΣΗ"
        elif change_pct >= 5:
            alert.append(f"Τιμή +{change_pct:.2f}% ➜ ΜΕΡΙΚΗ ΠΩΛΗΣΗ")
            recommendation = "ΜΕΡΙΚΗ ΠΩΛΗΣΗ"
        elif change_pct <= -3:
            alert.append(f"Τιμή {change_pct:.2f}% ➜ ΣΤΟΠ ΖΗΜΙΑΣ")
            recommendation = "ΣΤΟΠ ΖΗΜΙΑΣ"

        if last < 0.1:
            price_str = f"{last:.8f}"
            entry_str = f"{entry:.8f}"
        else:
            price_str = f"{last:.4f}"
            entry_str = f"{entry:.4f}"

        msg = (
            f"{symbol} (${price_str})\n"
            f"Entry: ${entry_str}\n"
            f"Change: {change_pct:.2f}%\n"
            + "\n".join(alert)
            + f"\nΠροτείνεται {recommendation}"
        )

        print(msg)
        send_push(msg)

if __name__ == "__main__":
    main()
