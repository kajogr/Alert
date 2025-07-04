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

        # Διάλεξε format ανάλογα με την τιμή
        if last < 0.1:
            price_str = f"{last:.8f}"
        else:
            price_str = f"{last:.4f}"

        msg = f"{symbol} (${price_str})\n" + "\n".join(alert if alert else ["🚨 No strong signal"]) + f"\n{recommendation}"
        send_push(msg)
        sent = True

    if not sent:
        send_push("🚨 TEST ALERT: No valid data but push works!")
