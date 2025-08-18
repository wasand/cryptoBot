def ema(values, period):
    if not values or period <= 1:
        return values[-1] if values else None
    k = 2 / (period + 1)
    ema_val = values[0]
    for v in values[1:]:
        ema_val = v * k + ema_val * (1 - k)
    return ema_val
