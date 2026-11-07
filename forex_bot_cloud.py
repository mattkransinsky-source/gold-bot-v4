import os
import time
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running - Step 2 signals"

def get_closes():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?range=1d&interval=1m"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    j = r.json()
    closes = j["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    closes = [c for c in closes if c is not None]
    return closes

def run_bot():
    while True:
        try:
            closes = get_closes()
            price = closes[-1]
            # Simple strategy: fast average vs slow average
            fast = sum(closes[-5:]) / 5
            slow = sum(closes[-20:]) / 20
            if fast > slow:
                signal = "BUY signal"
            elif fast < slow:
                signal = "SELL signal"
            else:
                signal = "HOLD"
            print(f"EURUSD: {price} | Fast: {fast:.5f} Slow: {slow:.5f} -> {signal}", flush=True)
        except Exception as e:
            print(f"Price fetch failed: {e}", flush=True)
        time.sleep(30)

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
