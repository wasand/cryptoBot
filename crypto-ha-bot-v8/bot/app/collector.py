from .binance_client import get_client
from .database import get_session
from .models import MarketData, FxRate, EquityPrice
from .config import settings
from .utils import ema, macd, atr
from datetime import datetime
import requests
import yfinance as yf
import uuid

def fetch_data_cycle():
    batch_id = str(uuid.uuid4())
    fetch_and_store_pairs(settings.DEFAULT_PAIRS, batch_id)
    fetch_fx(batch_id)
    fetch_equities(batch_id)

def fetch_and_store_pairs(pairs: list[str], batch_id: str):
    client = get_client()
    s = get_session()
    for pair in pairs:
        klines = client.klines(pair, '5m', limit=26)
        if not klines:
            continue
        prices = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        trades_5m = int(klines[-1][8]) if len(klines[-1]) > 8 else 0
        tph = trades_5m * 12
        row = MarketData(
            batch_id=batch_id, ts=datetime.utcnow(), pair=pair, price=prices[-1], volume=volumes[-1],
            trades_per_hour=tph, ema_fast=ema(prices, 12), ema_slow=ema(prices, 26),
            macd=macd(prices, 12, 26, 9), atr=atr(prices, 14)
        )
        s.add(row)
    s.commit(); s.close()

def fetch_fx(batch_id: str):
    if not settings.FX_ENABLED:
        return
    url = "http://api.nbp.pl/api/exchangerates/tables/A?format=json"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()[0]["rates"]
        rates = {r["code"]: r["mid"] for r in data if r["code"] in ["PLN", "EUR", "GBP", "CHF"]}
        s = get_session()
        for q, r in rates.items():
            s.add(FxRate(batch_id=batch_id, base="USD", quote=q, rate=float(r)))
        s.commit(); s.close()
    except Exception as e:
        print(f"FX fetch error: {e}")

def fetch_equities(batch_id: str):
    if not settings.EQUITIES_ENABLED:
        return
    symbols = ["BLK", "IVV", "VOO"]
    s = get_session()
    for sym in symbols:
        ticker = yf.Ticker(sym)
        data = ticker.history(period="1h")
        if not data.empty:
            price = data["Close"].iloc[-1]
            s.add(EquityPrice(batch_id=batch_id, ts=datetime.utcnow(), symbol=sym, price=price))
    s.commit(); s.close()