from .binance_client import get_client
from .database import get_session
from .models import MarketData, FxRate, EquityPrice
from .config import settings
from .utils import ema
from datetime import datetime
import requests

def fetch_and_store_pairs(pairs: list[str]):
    client = get_client()
    s = get_session()
    for pair in pairs:
        # 12 ostatnich świec 5m do EMA (ok. 1h)
        klines = client.klines(pair, '5m', limit=12)
        if not klines: 
            continue
        prices = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        trades_5m = int(klines[-1][8]) if len(klines[-1]) > 8 else 0
        tph = trades_5m * 12
        row = MarketData(
            ts=datetime.utcnow(), pair=pair, price=prices[-1], volume=volumes[-1], 
            trades_per_hour=tph, ema_fast=ema(prices, 12), ema_slow=ema(prices, 26)
        )
        s.add(row)
    s.commit(); s.close()

def fetch_fx():
    if not settings.FX_ENABLED:
        return
    # Prosty bezpłatny endpoint
    url = "https://api.exchangerate.host/latest?base=USD&symbols=PLN,EUR,GBP,CHF"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        rates = data.get("rates", {})
        s = get_session()
        for q, r in rates.items():
            s.add(FxRate(base="USD", quote=q, rate=float(r)))
        s.commit(); s.close()
    except Exception:
        pass

def fetch_equities():
    if not settings.EQUITIES_ENABLED:
        return
    # Placeholder: bez kluczy użyjmy przykładowych symboli i pseudo‑danych (dla testów)
    symbols = ["BLK", "IVV", "VOO"]
    s = get_session()
    now = datetime.utcnow()
    import random
    for sym in symbols:
        price = 100 + random.random()*50
        s.add(EquityPrice(ts=now, symbol=sym, price=price))
    s.commit(); s.close()
