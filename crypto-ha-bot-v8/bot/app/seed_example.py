from datetime import datetime, timedelta
from random import random
from .database import get_session, engine, Base
from .models import MarketData, PairConfig, FxRate, EquityPrice
import uuid

def seed():
    Base.metadata.create_all(bind=engine)
    s = get_session()
    batch_id = str(uuid.uuid4())
    now = datetime.utcnow()
    for pair, base in [("BTCUSDC", 60000.0), ("ETHUSDC", 3000.0)]:
        for i in range(100):
            ts = now - timedelta(minutes=5*(100-i))
            price = base * (1 + (random()-0.5)*0.02)
            md = MarketData(
                batch_id=batch_id, ts=ts, pair=pair, price=price, volume=10000*(1+random()),
                trades_per_hour=int(400+200*random()), ema_fast=price, ema_slow=price,
                macd=0.0, atr=price*0.01
            )
            s.add(md)
        s.add(PairConfig(pair=pair, allowed=True, risk_level=5))
    s.add(FxRate(batch_id=batch_id, base="USD", quote="PLN", rate=4.0))
    s.add(FxRate(batch_id=batch_id, base="USD", quote="EUR", rate=0.9))
    s.add(EquityPrice(batch_id=batch_id, symbol="BLK", price=800.0))
    s.commit(); s.close()
    print("Seeded example data")

if __name__ == "__main__":
    seed()