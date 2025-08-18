from dataclasses import dataclass
from typing import Literal, Tuple
from datetime import datetime, timedelta
from .pnl import latest_price, peak_since, last_tph

@dataclass
class StrategyParams:
    min_profit_pct: float = 5.0
    hysteresis_pct: float = 1.0
    buy_drawdown_pct: float = 3.0
    min_trades_per_hour: int = 100
    base_package_usd: float = 50.0
    downtrend_multiplier: float = 2.0
    buy_lookback: Literal["day","week","month"] = "day"

class SimpleStrategy:
    name = "SIMPLE_MINPROFIT_HYST"
    def __init__(self, params: StrategyParams):
        self.p = params

    def should_buy(self, pair: str, price_now: float, ref_low: float, trades_per_hour: int, is_downtrend: bool) -> Tuple[bool, str, float]:
        if trades_per_hour < self.p.min_trades_per_hour:
            return False, "Za mało transakcji/h", 0.0
        if ref_low > 0:
            dd = (price_now - ref_low) / ref_low * 100.0
            if dd <= self.p.buy_drawdown_pct:
                mult = self.p.downtrend_multiplier if is_downtrend else 1.0
                return True, f"Cena blisko minimum ({self.p.buy_lookback}), dd={dd:.2f}%", mult
        if is_downtrend:
            return True, "Dokupka w downtrendzie", self.p.downtrend_multiplier
        return False, "Warunki kupna niespełnione", 0.0

    def should_sell(self, price_now: float, entry_price: float, peak_since_entry: float):
        growth_pct = (price_now - entry_price) / entry_price * 100.0
        if growth_pct >= self.p.min_profit_pct:
            drop_from_peak = (peak_since_entry - price_now) / peak_since_entry * 100.0 if peak_since_entry > 0 else 0.0
            if drop_from_peak >= self.p.hysteresis_pct:
                return True, f"Min zysk + histereza (spadek od szczytu {drop_from_peak:.2f}%)"
            return False, "Min zysk, ale trend rosnący"
        return False, "Za mały zysk"