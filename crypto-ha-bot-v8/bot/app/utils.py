def ema(values, period):
    if not values or period <= 1:
        return values[-1] if values else None
    k = 2 / (period + 1)
    ema_val = values[0]
    for v in values[1:]:
        ema_val = v * k + ema_val * (1 - k)
    return ema_val

def macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow:
        return None
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    return ema_fast - ema_slow

def atr(prices, period=14):
    if len(prices) < period:
        return None
    trs = [max(prices[i] - prices[i-1], abs(prices[i] - prices[i-1])) for i in range(1, len(prices))]
    return sum(trs[-period:]) / period if trs else None