from .database import get_session
from .models import MarketData, Package
from sqlalchemy import select

def latest_price(pair: str) -> float | None:
    s = get_session()
    q = s.execute(select(MarketData).where(MarketData.pair==pair).order_by(MarketData.ts.desc())).scalars().first()
    s.close()
    if not q: return None
    try:
        return float(q.price)
    except:
        return None

def package_unrealized_pnl_usd(pkg: Package, price_now: float) -> float:
    qty = float(pkg.quantity)
    entry = float(pkg.entry_price)
    return (price_now - entry) * qty
