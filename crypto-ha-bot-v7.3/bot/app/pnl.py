from .database import get_session
from .models import MarketData
from sqlalchemy import select, func

def latest_price(pair: str) -> float | None:
    s = get_session()
    q = s.execute(select(MarketData.price).where(MarketData.pair==pair).order_by(MarketData.ts.desc()).limit(1)).scalar()
    s.close()
    return float(q) if q is not None else None

def last_points(pair: str, limit: int = 100):
    s = get_session()
    rows = s.execute(select(MarketData.ts, MarketData.price).where(MarketData.pair==pair).order_by(MarketData.ts.desc()).limit(limit)).all()
    s.close()
    rows = list(reversed(rows))
    return [{"ts": r[0].isoformat(), "price": float(r[1])} for r in rows]

def peak_since(pair: str, since_ts):
    s = get_session()
    m = s.execute(select(func.max(MarketData.price)).where(MarketData.pair==pair, MarketData.ts >= since_ts)).scalar()
    s.close()
    return float(m) if m is not None else None

def last_tph(pair: str) -> int:
    s = get_session()
    v = s.execute(select(MarketData.trades_per_hour).where(MarketData.pair==pair).order_by(MarketData.ts.desc()).limit(1)).scalar()
    s.close()
    return int(v or 0)
