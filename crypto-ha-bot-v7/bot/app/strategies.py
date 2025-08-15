from dataclasses import dataclass

@dataclass
class StrategyParams:
    min_profit_pct: float = 5.0
    hysteresis_pct: float = 1.0
    buy_drawdown_pct: float = 3.0
    min_trades_per_hour: int = 100
    base_package_usd: float = 50.0
    downtrend_multiplier: float = 2.0

class SimpleStrategy:
    name = "SIMPLE_MINPROFIT_HYST"
    def __init__(self, params: StrategyParams):
        self.p = params
    def should_buy(self, price_now: float, day_low: float, trades_per_hour: int, is_downtrend: bool):
        if trades_per_hour < self.p.min_trades_per_hour:
            return False, "Za mało transakcji/h"
        if (day_low > 0) and ((price_now - day_low) / day_low * 100.0 <= self.p.buy_drawdown_pct):
            return True, "Cena blisko minimum dnia"
        if is_downtrend:
            return True, "Dokupka w downtrendzie"
        return False, "Warunki kupna niespełnione"
    def should_sell(self, price_now: float, entry_price: float, peak_since_entry: float):
        growth_pct = (price_now - entry_price) / entry_price * 100.0
        if growth_pct >= self.p.min_profit_pct:
            drop_from_peak = (peak_since_entry - price_now) / peak_since_entry * 100.0 if peak_since_entry>0 else 0.0
            if drop_from_peak >= self.p.hysteresis_pct:
                return True, "Min zysk + histereza"
            return False, "Min zysk, ale trend rosnący"
        return False, "Za mały zysk"
