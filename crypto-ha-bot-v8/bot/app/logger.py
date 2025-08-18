from .database import get_session
from .models import TradeLog, Alert

def log(pair: str, message: str, level: str="INFO", pnl_usd: float|None=None, pnl_percent: float|None=None, strategy: str|None=None):
    s = get_session()
    row = TradeLog(pair=pair, message=message, level=level, pnl_usd=pnl_usd, pnl_percent=pnl_percent, strategy=strategy)
    s.add(row); s.commit(); s.close()

def add_alert(pair: str, pnl_usd: float, pnl_percent: float, alert_type: str):
    s = get_session()
    row = Alert(pair=pair, pnl_usd=pnl_usd, pnl_percent=pnl_percent, type=alert_type)
    s.add(row); s.commit(); s.close()