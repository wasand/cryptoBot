from .database import get_session
from .models import TradeLog, Alert
from datetime import datetime

def log(pair: str, message: str, level: str, pnl_usd: float = None, pnl_percent: float = None, strategy: str = None):
    s = get_session()
    row = TradeLog(
        ts=datetime.utcnow(),  # Poprawka: ustawiamy aktualny timestamp UTC
        pair=pair,
        level=level,
        message=message,
        pnl_usd=pnl_usd,
        pnl_percent=pnl_percent,
        strategy=strategy
    )
    s.add(row)
    s.commit()
    s.close()

def add_alert(pair: str, pnl_usd: float, pnl_percent: float, type: str):
    s = get_session()
    row = Alert(
        ts=datetime.utcnow(),
        pair=pair,
        pnl_usd=pnl_usd,
        pnl_percent=pnl_percent,
        type=type
    )
    s.add(row)
    s.commit()
    s.close()
