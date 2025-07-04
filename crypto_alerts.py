import requests
import pandas as pd
from datetime import datetime
import os

# Pushover secrets από GitHub
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

# Τα CoinGecko ids για τα κέρματα σου
coins = {
    "SOL": "solana",
    "IOTX": "iotex",
    "SUI": "sui",
    "ETH": "ethereum",
    "PEPE": "pepe",
    "SAGA": "saga"
}

# Παίρνει daily prices (30 μέρες) από CoinGecko
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

# Στέλνει push στο Pushover
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

# Κύρια λογική
def main():
    print(f"🔔 Crypto Alerts @ {datetime.now()}")
    sent = False

    # Entry prices (ξεκινάνε από την τρέχουσα τιμή)
    entry_prices = {}

    for symbol, coin_id in coins.items():
        print(f"\n🔎 Checking {symbol} ({coin_id})")
        prices = get_prices(coin_id)
        print(f"Prices: last 5 → {prices[-5:]}")

        if not prices:
            print(f"⏭️ No data for {symbol}, skipping...")
            continue

        last = prices[-1]

        # Αν δεν έχουμε entry ➜ παίρνουμε το τρέχον
        if symbol not in entry_prices:
            entry_prices[symbol] = last

        entry = entry_prices[symbol]
        change_pct = ((last - entry) / entry) * 100

        print(f"Last price: {last} | Entry: {entry} | Change: {change_pct:.2f}%")

        rsi = calc_rsi(prices)
        ma = calc_ma(prices)
        macd, signal = calc_macd(prices)

        print(f"RSI: {rsi:.2f} | MA: {ma:.4f} | MACD: {macd:.4f} | Signal: {signal:.4f}")

        alert = []
        recommendation = "Προτείνεται ΑΝΑΜΟΝΗ"

        if rsi < 30:
            alert.append("RSI κάτω από 30 (υπερπώληση)")
            recommendation = "Προτείνεται ΑΓΟΡΑ"
        elif rsi > 70:
            alert.append("RSI πάνω από 70 (υπεραγορά)")
            recommendation = "Προτείνεται ΟΧΙ ΑΓΟΡΑ"

        if macd > signal:
            alert.append("MACD bullish crossover")
            recommendation = "Προτείνεται ΑΓΟΡΑ"
        elif macd < signal:
            alert.append("MACD bearish crossover")
            recommendation = "Προτείνεται ΟΧΙ ΑΓΟΡΑ"

        if last > ma:
            alert.append("Τιμή πάνω από MA20 (breakout)")
            recommendation = "Προτείνεται ΑΓΟΡΑ"
        elif last < ma:
            alert.append("Τιμή κάτω από MA20 (breakdown)")
            recommendation = "Προτείνεται ΟΧΙ ΑΓΟΡΑ"

        # Ολική πώληση αν διπλασιαστεί
        if change_pct >= 100:
            alert.append(f"+{change_pct:.2f}% από το entry ➜ Σήμα ΟΛΙΚΗΣ ΠΩΛΗΣΗΣ")
            recommendation = "Προτείνεται ΟΛΙΚΗ ΠΩΛΗΣΗ"
        elif change_pct >= 5:
            alert.append(f"+{change_pct:.2f}% από το entry ➜ Σήμα ΜΕΡΙΚΗΣ ΠΩΛΗΣΗΣ")
            recommendation = "Προτείνεται ΜΕΡΙΚΗ ΠΩΛΗΣΗ"
        elif change_pct <= -3:
            alert.append(f"{change_pct:.2f}% από το entry ➜ Σήμα ΣΤΟΠ ΖΗΜΙΑΣ")
            recommendation = "Προτείνεται ΣΤΟΠ ΖΗΜΙΑΣ"

        if last < 0.1:
            price_str = f"{last:.8f}"
        else:
            price_str = f"{last:.4f}"

        msg = f"{symbol} (${price_str})\nEntry: ${entry:.4f}\nChange: {change_pct:.2f}%\n" + "\n".join(alert if alert else ["🚨 No strong signal"]) + f"\n{recommendation}"
        print(f"📤 Sending push: {msg}")

        send_push(msg)
        sent = True

    if not sent:
        print("⚠️ No valid data — sending fallback TEST push...")
        send_push("🚨 TEST ALERT: No valid data but push works!")

if __name__ == "__main__":
    main()
