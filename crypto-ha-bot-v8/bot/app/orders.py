from .binance_client import get_client
from .database import get_session
from .models import Package
from .logger import log
from .pnl import latest_price, latest_fx_rate
from datetime import datetime

def market_buy_package(pair: str, quote_amount_usd: float):
    client = get_client()
    try:
        price = float(client.ticker_price(pair)["price"])
        quantity = quote_amount_usd / price
        with get_session() as session:
            pkg = Package(
                pair=pair,
                created_at=datetime.utcnow(),
                quantity=quantity,
                entry_price=price,
                bought_at=datetime.utcnow()
            )
            session.add(pkg)
            session.commit()
            log(pair, f"Buy: {quantity:.6f} @ {price:.2f} USD", "INFO")
            return {"id": pkg.id, "pair": pair, "quantity": quantity, "entry_price": price}
    except Exception as e:
        log(pair, f"Buy error: {e}", "ERROR")
        raise

def market_sell_package(package_id: int, pair: str, quantity: float):
    client = get_client()
    try:
        price = float(client.ticker_price(pair)["price"])
        fx_rate = latest_fx_rate("USD", "PLN") or 4.0  # Domyślny kurs PLN
        with get_session() as session:
            pkg = session.query(Package).filter(Package.id == package_id).first()
            if not pkg or pkg.sold_at:
                raise Exception("Package not found or already sold")
            pkg.exit_price = price
            pkg.sold_at = datetime.utcnow()
            pkg.realized_pnl_usd = (price - pkg.entry_price) * quantity
            pkg.realized_pnl_pln = pkg.realized_pnl_usd * fx_rate
            session.commit()
            log(pair, f"Sell: {quantity:.6f} @ {price:.2f} USD, PNL: {pkg.realized_pnl_usd:.2f} USD, {pkg.realized_pnl_pln:.2f} PLN", "INFO")
            return {"id": package_id, "pair": pair, "exit_price": price, "realized_pnl_usd": pkg.realized_pnl_usd, "realized_pnl_pln": pkg.realized_pnl_pln}
    except Exception as e:
        log(pair, f"Sell error: {e}", "ERROR")
        raise
