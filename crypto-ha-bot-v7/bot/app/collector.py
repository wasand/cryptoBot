from .binance_client import get_client
from .database import get_session
from .models import MarketData
from datetime import datetime

def fetch_and_store_pairs(pairs: list[str]):
    client = get_client()
    s = get_session()
    for pair in pairs:
        klines = client.klines(pair, '5m', limit=1)
        if not klines:
            continue
        k = klines[0]
        close = float(k[4])
        volume = float(k[5])
        trades_5m = int(k[8]) if len(k) > 8 else 0
        tph = trades_5m * 12
        row = MarketData(ts=datetime.utcnow(), pair=pair, price=str(close), volume=str(volume), trades_per_hour=tph)
        s.add(row)
    s.commit(); s.close()
