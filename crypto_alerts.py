import requests
import pandas as pd
from datetime import datetime
import os

# Pushover
import http.client, urllib

PUSHOVER_USER = os.getenv('PUSHOVER_USER')
PUSHOVER_TOKEN = os.getenv('PUSHOVER_TOKEN')

symbols = {
    'PEPEUSDC': 0.000000097,
    'SUIUSDC': 2.92,
    'ETHUSDC': 2550.00,
    'IOTXUSDC': 0.0212,
    'SOLUSDC': 150.00,
    'SAGAUSDC': 0.21
}

for symbol, entry_price in symbols.items():
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=100"
    data = requests.get(url).json()
    closes = [float(k[4]) for k in data]

    df = pd.DataFrame(closes, columns=['Close'])
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    latest = df.iloc[-1]
    current_price = latest['Close']
    rsi = latest['RSI']
    macd_cross = latest['MACD'] > latest['Signal']
    ma20 = latest['MA20']
    ma50 = latest['MA50']
    change = ((current_price - entry_price) / entry_price) * 100

    condition = []
    if rsi < 30:
        condition.append("RSI κάτω από 30 ➜ Υπερπώληση")
    if macd_cross:
        condition.append("MACD bullish crossover")
    else:
        condition.append("MACD bearish crossover")
    if current_price > ma20:
        condition.append("Τιμή πάνω από MA20 ➜ Breakout")
    else:
        condition.append("Τιμή κάτω από MA20 ➜ Breakdown")

    if change >= 100:
        condition.append(f"Τιμή +{change:.2f}% ➜ ΟΛΙΚΗ ΠΩΛΗΣΗ")
        recommendation = "Προτείνεται ΠΩΛΗΣΗ"
    elif rsi < 30 and macd_cross and current_price > ma20:
        recommendation = "Προτείνεται ΑΓΟΡΑ"
    else:
        recommendation = "Προτείνεται ΟΧΙ ΑΓΟΡΑ"

    # ✔️ FORMAT για PEPE
    if symbol.startswith('PEPE'):
        price_str = f"${current_price:.8f}"
        entry_str = f"${entry_price:.8f}"
    else:
        price_str = f"${current_price:.4f}"
        entry_str = f"${entry_price:.4f}"

    message = f"{symbol.replace('USDC','')} ({price_str})\nEntry: {entry_str}\nChange: {change:.2f}%\n"
    message += "\n".join(condition) + f"\n{recommendation}"

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "message": message,
      }), { "Content-type": "application/x-www-form-urlencoded" })

    print(message)
