from .config import settings
from .database import engine
from .binance_client import get_client
from sqlalchemy import text

def check_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True

def check_binance():
    client = get_client()
    exch = client.exchange_info()
    return len(exch.get("symbols", []))

def is_quote_allowed(pair: str) -> bool:
    # Na końcu pary zwykle jest quote (np. BTCUSDC -> USDC)
    for q in settings.ALLOWED_QUOTES:
        if pair.endswith(q):
            return True
    return False
