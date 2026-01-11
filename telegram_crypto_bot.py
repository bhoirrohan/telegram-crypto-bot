import ccxt
import pandas as pd
import ta
import requests
import time
from datetime import datetime

# ========== TELEGRAM CONFIG ==========
BOT_TOKEN = "8429666406:AAHnBa0Ay2BCq6ENkqc2rY8ObSCiUgyn5vM"
CHAT_ID = "1733836784"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# ========== MARKET CONFIG ==========
symbol = "BTC/USDT"
timeframe = "15m"
limit = 200

exchange = ccxt.binance()

last_alert_time = None

print("🚀 Telegram BTC 15m Signal Bot Started")

while True:
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(
            ohlcv,
            columns=["time","open","high","low","close","volume"]
        )
        df["time"] = pd.to_datetime(df["time"], unit="ms")

        # Indicators
        df["ema20"] = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
        df["ema50"] = ta.trend.EMAIndicator(df["close"], 50).ema_indicator()
        df["rsi"] = ta.momentum.RSIIndicator(df["close"], 14).rsi()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        price = last["close"]

        trend_now = abs(last["ema20"] - last["ema50"]) / price
        trend_prev = abs(prev["ema20"] - prev["ema50"]) / prev["close"]

        # ===== CONDITIONS =====
        cond_ema = last["ema20"] > last["ema50"]
        cond_rsi = 50 < last["rsi"] < 60
        cond_trend = trend_now > 0.0005 and trend_now > trend_prev

        if cond_ema and cond_rsi and cond_trend:
            candle_time = last["time"]

            if candle_time != last_alert_time:
                last_alert_time = candle_time

                msg = (
                    f"🟢 <b>BTC 15m BUY SETUP</b>\n\n"
                    f"Price: {round(price, 2)}\n"
                    f"EMA20 > EMA50\n"
                    f"RSI: {round(last['rsi'], 2)}\n"
                    f"Trend expanding\n\n"
                    f"Action: CHECK CHART"
                )

                send_telegram(msg)
                print("Signal sent at", candle_time)

        time.sleep(60)

    except Exception as e:
        print("Error:", e)
        time.sleep(60)
