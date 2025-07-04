def main():
    sent = False
    for symbol, coin_id in coins.items():
        print(f"🔎 Checking {symbol}...")
        prices = get_prices(coin_id)
        print(f"Prices fetched: {prices[-5:]}")

        if not prices:
            print(f"⏭️ No data for {symbol}, skipping...")
            continue

        last = prices[-1]
        print(f"Last price: {last}")

        rsi = calc_rsi(prices)
        ma = calc_ma(prices)
        macd, signal = calc_macd(prices)

        print(f"RSI: {rsi:.2f}, MA: {ma:.2f}, MACD: {macd:.2f}, Signal: {signal:.2f}")

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

        if last < 0.1:
            price_str = f"{last:.8f}"
        else:
            price_str = f"{last:.4f}"

        msg = f"{symbol} (${price_str})\n" + "\n".join(alert if alert else ["🚨 No strong signal"]) + f"\n{recommendation}"
        print(f"📤 Sending push: {msg}")
        send_push(msg)
        sent = True

    if not sent:
        print("⚠️ No valid symbols, sending fallback TEST push...")
        send_push("🚨 TEST ALERT: No valid data but push works!")
