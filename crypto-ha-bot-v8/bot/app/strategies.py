from dataclasses import dataclass
from datetime import datetime, timedelta
from .pnl import peak_since, last_tph
from .database import get_session
from .models import Package

@dataclass
class StrategyParams:
    min_profit_pct: float
    hysteresis_pct: float
    buy_drawdown_pct: float
    min_trades_per_hour: int
    base_package_usd: float
    downtrend_multiplier: float
    buy_lookback: str

class SimpleStrategy:
    def __init__(self, params: StrategyParams):
        self.params = params
        self.name = "SIMPLE_MINPROFIT_HYST"

    def should_buy(self, pair: str, price_now: float, ref_low: float, tph: float, is_downtrend: bool):
        if price_now <= 0 or ref_low <= 0 or tph < self.params.min_trades_per_hour:
            return False, "Invalid data or low trading activity", 1.0

        # Sprawdź, czy cena jest najniższa w okresie lookback
        drawdown = (ref_low - price_now) / ref_low * 100 if ref_low > 0 else 0
        is_lowest = price_now <= ref_low  # Cena musi być najniższa, a nie tylko blisko minimum

        # Sprawdź otwarte pakiety
        s = get_session()
        open_pkgs = s.query(Package).filter(Package.pair == pair, Package.sold_at.is_(None)).all()
        s.close()

        multiplier = 1.0
        if open_pkgs:
            # Jeśli mamy otwarte pakiety, zwiększ mnożnik
            multiplier = self.params.downtrend_multiplier
            # Sprawdź, czy cena jest niższa niż średnia cena wejścia
            avg_entry = sum(p.entry_price * p.quantity for p in open_pkgs) / sum(p.quantity for p in open_pkgs)
            if price_now >= avg_entry * (1 + self.params.hysteresis_pct / 100):
                return False, f"Price above hysteresis threshold (avg_entry={avg_entry:.2f})", 1.0

        if is_lowest and is_downtrend:
            return True, f"Price at lowest in {self.params.buy_lookback}, dd={drawdown:.2f}%", multiplier
        return False, f"Price not lowest in {self.params.buy_lookback}", 1.0
