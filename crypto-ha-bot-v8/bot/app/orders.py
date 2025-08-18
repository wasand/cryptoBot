from .binance_client import get_client
from .database import get_session
from .models import Package, FxRate
from .logger import log
from datetime import datetime
from sqlalchemy import select

def get_latest_fx_rate(quote: str = "PLN") -> float:
    s = get_session()
    rate = s.execute(select(FxRate.rate).where(FxRate.quote==quote).order_by(FxRate.ts.desc()).limit(1)).scalar()
    s.close()
    return float(rate) if rate else 4.0

def market_buy_package(pair: str, quote_amount_usd: float):
    client = get_client()
    order = client.new_order(symbol=pair, side='BUY', type='MARKET', quoteOrderQty=str(quote_amount_usd))
    qty = float(order.get('executedQty', 0))
    avg_price = None
    if 'cummulativeQuoteQty' in order and qty>0:
        avg_price = float(order['cummulativeQuoteQty'])/qty
    elif order.get('fills'):
        total = sum(float(f['price']) * float(f['qty']) for f in order['fills'])
        qty = sum(float(f['qty']) for f in order['fills'])
        avg_price = total/qty if qty>0 else 0.0

    s = get_session()
    pkg = Package(pair=pair, quantity=qty, entry_price=avg_price or 0.0, created_at=datetime.utcnow())
    s.add(pkg); s.commit()
    pid = pkg.id
    s.close()
    log(pair, f"KUPNO pakietu: id={pid} qty={qty:.8f}, entry={avg_price:.6f}", "INFO", strategy="AUTOTRADE/HA")
    return {"package_id": pid, "order": order}

def market_sell_package(package_id: int, pair: str, qty: float):
    client = get_client()
    order = client.new_order(symbol=pair, side='SELL', type='MARKET', quantity=str(qty))
    price = None
    if order.get('fills'):
        total = sum(float(f['price']) * float(f['qty']) for f in order['fills'])
        q = sum(float(f['qty']) for f in order['fills'])
        price = total/q if q>0 else None
    elif 'price' in order:
        price = float(order['price'])

    s = get_session()
    pkg = s.query(Package).filter(Package.id==package_id).first()
    if pkg and not pkg.sold_at:
        pkg.exit_price = price or pkg.entry_price
        pkg.sold_at = datetime.utcnow()
        pkg.realized_pnl_usd = (pkg.exit_price - pkg.entry_price) * pkg.quantity
        pkg.realized_pnl_pln = pkg.realized_pnl_usd * get_latest_fx_rate("PLN")
        s.commit()
        log(pair, f"SPRZEDAŻ pakietu: id={pkg.id} qty={pkg.quantity:.8f}, exit={pkg.exit_price:.6f}, pnl={pkg.realized_pnl_usd:.2f} USD, {pkg.realized_pnl_pln:.2f} PLN", "INFO", pnl_usd=pkg.realized_pnl_usd)
    s.close()
    return {"order": order}