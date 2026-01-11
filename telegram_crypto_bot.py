import time
import requests
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from telegram import Bot

# ================= CONFIG =================
BOT_TOKEN = "8429666406:AAHnBa0Ay2BCq6ENkqc2rY8ObSCiUgyn5vM"
CHAT_ID = "1733836784"

SYMBOL = "BTCUSDT"
INTERVAL = "15"
BYBIT_URL = "https://api.bybit.com/v5/market/kline"

# Strategy params
EMA_FAST = 20
EMA_SLOW = 50
RSI_LOW = 50
RSI_HIGH = 60

# =========================================

bot = Bot(token=BOT_TOKEN)
last_signal_time = None

def fetch_klines():
    params = {
        "category": "linear",
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": 200
    }
    r = requests.get(BYBIT_URL, params=params, timeout=10)
    data = r.json()["result"]["list"]
    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume","turnover"
    ])
    df["close"] = df["close"].astype(float)
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df.sort_values("time")

def check_signal():
    global last_signal_time

    df = fetch_klines()

    ema20 = EMAIndicator(df["close"], EMA_FAST).ema_indicator()
    ema50 = EMAIndicator(df["close"], EMA_SLOW).ema_indicator()
    rsi = RSIIndicator(df["close"], 14).rsi()

    df["ema20"] = ema20
    df["ema50"] = ema50
    df["rsi"] = rsi

    latest = df.iloc[-1]

    buy_condition = (
        latest["ema20"] > latest["ema50"] and
        RSI_LOW <= latest["rsi"] <= RSI_HIGH
    )

    if buy_condition and last_signal_time != latest["time"]:
        last_signal_time = latest["time"]

        message = f"""
🟢 BTC BUY SIGNAL (15m)

Price: {latest['close']}
EMA20 > EMA50
RSI: {latest['rsi']:.2f}

⏱ Candle Closed
⚠️ Not Financial Advice
        """
        bot.send_message(chat_id=CHAT_ID, text=message)

while True:
    try:
        print("🔍 Checking BTC 15m...")
        check_signal()
        time.sleep(60)
    except Exception as e:
        print("Error:", e)
        time.sleep(60)
