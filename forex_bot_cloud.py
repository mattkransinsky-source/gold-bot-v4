import os
import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PAIR = "GC=F"
BALANCE = 1000.0
RISK_PER_TRADE = 0.01
STOP_LOSS_DOLLARS = 5.0   # WINNER: Tight $5 SL
TAKE_PROFIT_DOLLARS = 10.0 # WINNER: $10 TP = 1:2

balance = BALANCE
in_trade = None
entry_price = 0
breakeven_done = False

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        print("📩 Telegram sent")
    except Exception as e:
        print(f"Telegram failed: {e}")

print(f"🤖 GOLD BOT V4 - WINNER | Backtest: $1000 -> $1310 in 59 days | SL $5 TP $10")
send_telegram("🤖 Gold Bot V4 WINNER Started! Backtested: $1000 -> $1310. Strategy: EMA 9/21, SL $5 TP $10, Breakeven at +$5.")

while True:
    try:
        df = yf.download(PAIR, period="3d", interval="15m", progress=False)
        if df.empty:
            time.sleep(30); continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df['EMA_FAST'] = df['Close'].ewm(span=9).mean()
        df['EMA_SLOW'] = df['Close'].ewm(span=21).mean()
        last = df.iloc[-1]; prev = df.iloc[-2]
        price = float(last['Close'])
        now = datetime.now().strftime("%H:%M:%S")
        buy_cross = prev['EMA_FAST'] < prev['EMA_SLOW'] and last['EMA_FAST'] > last['EMA_SLOW']
        sell_cross = prev['EMA_FAST'] > prev['EMA_SLOW'] and last['EMA_FAST'] < last['EMA_SLOW']

        if in_trade == "BUY":
            if not breakeven_done and price >= entry_price + 5:
                breakeven_done = True
                msg = f"🔒 V4 BREAKEVEN! BUY now risk-free @ {entry_price:.2f}"
                print(f"[{now}] {msg}"); send_telegram(msg)
            if price >= entry_price + TAKE_PROFIT_DOLLARS:
                profit = BALANCE * RISK_PER_TRADE * 2; balance += profit
                msg = f"✅ V4 TAKE PROFIT +${profit:.2f}\nBUY @ {entry_price:.2f} -> {price:.2f} | Balance: ${balance:.2f}"
                print(f"[{now}] {msg}"); send_telegram(msg); in_trade=None; breakeven_done=False
            elif price <= entry_price - STOP_LOSS_DOLLARS:
                loss = 0 if breakeven_done else BALANCE * RISK_PER_TRADE
                balance -= loss
                msg = f"❌ V4 STOP LOSS -${loss:.2f}\nBUY @ {entry_price:.2f} -> {price:.2f} | Balance: ${balance:.2f}"
                print(f"[{now}] {msg}"); send_telegram(msg); in_trade=None; breakeven_done=False
        elif in_trade == "SELL":
            if not breakeven_done and price <= entry_price - 5:
                breakeven_done = True
                msg = f"🔒 V4 BREAKEVEN! SELL now risk-free @ {entry_price:.2f}"
                print(f"[{now}] {msg}"); send_telegram(msg)
            if price <= entry_price - TAKE_PROFIT_DOLLARS:
                profit = BALANCE * RISK_PER_TRADE * 2; balance += profit
                msg = f"✅ V4 TAKE PROFIT +${profit:.2f}\nSELL @ {entry_price:.2f} -> {price:.2f} | Balance: ${balance:.2f}"
                print(f"[{now}] {msg}"); send_telegram(msg); in_trade=None; breakeven_done=False
            elif price >= entry_price + STOP_LOSS_DOLLARS:
                loss = 0 if breakeven_done else BALANCE * RISK_PER_TRADE
                balance -= loss
                msg = f"❌ V4 STOP LOSS -${loss:.2f}\nSELL @ {entry_price:.2f} -> {price:.2f} | Balance: ${balance:.2f}"
                print(f"[{now}] {msg}"); send_telegram(msg); in_trade=None; breakeven_done=False

        if not in_trade:
            if buy_cross:
                in_trade="BUY"; entry_price=price; breakeven_done=False
                msg=f"🟢 V4 BUY!\nPrice: {price:.2f}\nSL: {price-5:.2f} | TP: {price+10:.2f}"
                print(f"[{now}] {msg}"); send_telegram(msg)
            elif sell_cross:
                in_trade="SELL"; entry_price=price; breakeven_done=False
                msg=f"🔴 V4 SELL!\nPrice: {price:.2f}\nSL: {price+5:.2f} | TP: {price-10:.2f}"
                print(f"[{now}] {msg}"); send_telegram(msg)
            else:
                print(f"[{now}] Waiting... Gold ${price:.2f} | EMA9 {last['EMA_FAST']:.2f} EMA21 {last['EMA_SLOW']:.2f}")
        time.sleep(60)
    except KeyboardInterrupt:
        send_telegram(f"Bot V4 stopped. Final Balance: ${balance:.2f}")
        print(f"\nBot stopped. Final Balance: ${balance:.2f}")
        break
    except Exception as e:
        print(f"Error: {e} - retrying in 30s")
        time.sleep(30)
