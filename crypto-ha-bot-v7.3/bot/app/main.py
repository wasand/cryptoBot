import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from .config import settings
from .database import engine, Base, get_session
from .models import MarketData, Package, TradeLog, Alert, PairConfig
from .collector import fetch_and_store_pairs, fetch_fx, fetch_equities
from .strategies import SimpleStrategy, StrategyParams
from .logger import log, add_alert
from .pnl import latest_price, last_points, peak_since, last_tph
from .checks import is_quote_allowed
from .binance_client import get_client

app = FastAPI(title="Crypto HA Bot v7.3", version="7.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

running = False
autotrade = settings.AUTO_TRADE
last_alert = {}
last_fx_fetch = None
last_eq_fetch = None

class StartBody(BaseModel):
    pairs: list[str] | None = None
    autotrade: bool | None = None

class BuyBody(BaseModel):
    pair: str
    quote_amount_usd: float

class SellBody(BaseModel):
    pair: str
    package_id: int | None = None  # jeśli None, sprzedaj wszystkie otwarte

class ConfigBody(BaseModel):
    min_profit_pct: float | None = None
    hysteresis_pct: float | None = None
    buy_drawdown_pct: float | None = None
    min_trades_per_hour: int | None = None
    base_package_usd: float | None = None
    downtrend_multiplier: float | None = None
    buy_lookback: str | None = None

class PairCfgBody(BaseModel):
    pair: str
    allowed: bool | None = None
    risk_level: int | None = None

@app.get("/health")
def health():
    return {"status":"ok","running":running, "autotrade": autotrade, "pairs": settings.DEFAULT_PAIRS}

@app.post("/start")
def start_bot(body: StartBody | None=None):
    global running, autotrade
    running = True
    if body:
        if body.pairs:
            settings.DEFAULT_PAIRS = [p.upper() for p in body.pairs if is_quote_allowed(p.upper())]
        if body.autotrade is not None:
            autotrade = body.autotrade
    return {"running": running, "autotrade": autotrade, "pairs": settings.DEFAULT_PAIRS}

@app.post("/stop")
def stop_bot():
    global running
    running = False
    return {"running": running}

@app.post("/autotrade")
def set_autotrade(flag: bool):
    global autotrade
    autotrade = bool(flag)
    return {"autotrade": autotrade}

@app.post("/order/buy")
def buy_package(body: BuyBody):
    from .orders import market_buy_package
    try:
        result = market_buy_package(body.pair.upper(), body.quote_amount_usd)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/order/sell")
def sell_packages(body: SellBody):
    from .orders import market_sell_package
    s = get_session()
    try:
        if body.package_id is not None:
            pkg = s.query(Package).filter(Package.id==body.package_id, Package.pair==body.pair.upper(), Package.sold_at.is_(None)).first()
            if not pkg:
                raise HTTPException(status_code=404, detail="Package not found or already sold")
            return market_sell_package(pkg.id, pkg.pair, pkg.quantity)
        else:
            pkgs = s.query(Package).filter(Package.pair==body.pair.upper(), Package.sold_at.is_(None)).all()
            res = []
            for p in pkgs:
                res.append(market_sell_package(p.id, p.pair, p.quantity))
            return {"sold_count": len(res), "orders": res}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        s.close()

@app.get("/logs")
def get_logs(limit: int = 100):
    s = get_session()
    rows = s.query(TradeLog).order_by(TradeLog.ts.desc()).limit(limit).all()
    s.close()
    return [{"ts": r.ts.isoformat(), "pair": r.pair, "level": r.level, "message": r.message, "pnl_usd": r.pnl_usd, "pnl_percent": r.pnl_percent, "strategy": r.strategy} for r in rows]

@app.get("/alerts")
def get_alerts(limit: int = 100):
    s = get_session()
    rows = s.query(Alert).order_by(Alert.ts.desc()).limit(limit).all()
    s.close()
    return [{"ts": r.ts.isoformat(), "pair": r.pair, "type": r.type, "pnl_usd": r.pnl_usd, "pnl_percent": r.pnl_percent} for r in rows]

@app.delete("/alerts")
def clear_alerts():
    s = get_session()
    s.query(Alert).delete()
    s.commit(); s.close()
    return {"cleared": True}

@app.get("/market/history")
def market_history(pair: str, limit: int = 100):
    return {"pair": pair.upper(), "points": last_points(pair.upper(), limit=limit)}

@app.get("/config")
def get_config():
    return {
        "min_profit_pct": settings.STRAT_MIN_PROFIT_PCT,
        "hysteresis_pct": settings.STRAT_HYSTERESIS_PCT,
        "buy_drawdown_pct": settings.STRAT_BUY_DRAWDOWN_PCT,
        "min_trades_per_hour": settings.STRAT_MIN_TRADES_PER_HOUR,
        "base_package_usd": settings.STRAT_BASE_PACKAGE_USD,
        "downtrend_multiplier": settings.STRAT_DOWNTREND_MULTIPLIER,
        "buy_lookback": settings.STRAT_BUY_LOOKBACK,
        "allowed_quotes": settings.ALLOWED_QUOTES,
    }

@app.put("/config")
def update_config(body: ConfigBody):
    if body.min_profit_pct is not None: settings.STRAT_MIN_PROFIT_PCT = float(body.min_profit_pct)
    if body.hysteresis_pct is not None: settings.STRAT_HYSTERESIS_PCT = float(body.hysteresis_pct)
    if body.buy_drawdown_pct is not None: settings.STRAT_BUY_DRAWDOWN_PCT = float(body.buy_drawdown_pct)
    if body.min_trades_per_hour is not None: settings.STRAT_MIN_TRADES_PER_HOUR = int(body.min_trades_per_hour)
    if body.base_package_usd is not None: settings.STRAT_BASE_PACKAGE_USD = float(body.base_package_usd)
    if body.downtrend_multiplier is not None: settings.STRAT_DOWNTREND_MULTIPLIER = float(body.downtrend_multiplier)
    if body.buy_lookback is not None: settings.STRAT_BUY_LOOKBACK = body.buy_lookback.lower()
    return get_config()

@app.get("/pair-config")
def get_pair_config():
    s = get_session()
    cfgs = s.query(PairConfig).all()
    s.close()
    return [{"pair": c.pair, "allowed": c.allowed, "risk_level": c.risk_level} for c in cfgs]

@app.put("/pair-config")
def put_pair_config(body: PairCfgBody):
    s = get_session()
    c = s.query(PairConfig).filter(PairConfig.pair==body.pair.upper()).first()
    if not c:
        c = PairConfig(pair=body.pair.upper(), allowed=True, risk_level=5)
        s.add(c)
    if body.allowed is not None: c.allowed = bool(body.allowed)
    if body.risk_level is not None: c.risk_level = max(0, min(10, int(body.risk_level)))
    s.commit(); s.close()
    return {"pair": c.pair, "allowed": c.allowed, "risk_level": c.risk_level}

async def loop_task():
    global last_fx_fetch, last_eq_fetch
    while True:
        if running:
            # kolektor krypto 5m
            fetch_and_store_pairs(settings.DEFAULT_PAIRS)

            # kolektory zewnętrzne wg interwału
            now = datetime.utcnow()
            if last_fx_fetch is None or (now - last_fx_fetch).total_seconds() >= 3600:
                fetch_fx(); last_fx_fetch = now
            if last_eq_fetch is None or (now - last_eq_fetch).total_seconds() >= 3600:
                fetch_equities(); last_eq_fetch = now

            # autotrade
            if autotrade:
                params = StrategyParams(
                    min_profit_pct=settings.STRAT_MIN_PROFIT_PCT,
                    hysteresis_pct=settings.STRAT_HYSTERESIS_PCT,
                    buy_drawdown_pct=settings.STRAT_BUY_DRAWDOWN_PCT,
                    min_trades_per_hour=settings.STRAT_MIN_TRADES_PER_HOUR,
                    base_package_usd=settings.STRAT_BASE_PACKAGE_USD,
                    downtrend_multiplier=settings.STRAT_DOWNTREND_MULTIPLIER,
                    buy_lookback=settings.STRAT_BUY_LOOKBACK,
                )
                strat = SimpleStrategy(params)

                client = get_client()

                for pair in settings.DEFAULT_PAIRS:
                    if not is_quote_allowed(pair):
                        continue

                    # pair-specific config
                    s = get_session()
                    pc = s.query(PairConfig).filter(PairConfig.pair==pair).first()
                    s.close()
                    allowed = pc.allowed if pc else True
                    risk_level = pc.risk_level if pc else 5
                    if not allowed:
                        log(pair, "Para wyłączona w konfiguracji", "DEBUG")
                        continue

                    # bieżące dane
                    price_now = latest_price(pair)
                    tph = last_tph(pair)

                    # EMA i downtrend
                    s = get_session()
                    last_md = s.query(MarketData).filter(MarketData.pair==pair).order_by(MarketData.ts.desc()).first()
                    s.close()
                    ema_fast = last_md.ema_fast if last_md else None
                    is_downtrend = (ema_fast is not None) and price_now is not None and price_now < ema_fast

                    # low wg lookback
                    ref_low = 0.0
                    try:
                        if settings.STRAT_BUY_LOOKBACK == "day":
                            t24 = client.ticker_24hr(symbol=pair)
                            ref_low = float(t24.get("lowPrice", 0) or 0)
                        else:
                            # week = 7d, month = 30d
                            days = 7 if settings.STRAT_BUY_LOOKBACK=="week" else 30
                            kl = client.klines(pair, '1h', limit=24*days)
                            lows = [float(k[3]) for k in kl]
                            ref_low = min(lows) if lows else 0.0
                    except Exception:
                        ref_low = 0.0

                    # SELL dla każdego pakietu
                    s = get_session()
                    open_pkgs = s.query(Package).filter(Package.pair==pair, Package.sold_at.is_(None)).all()
                    s.close()
                    for p in open_pkgs:
                        pk = peak_since(pair, p.created_at) or price_now or p.entry_price
                        sell, reason = strat.should_sell(price_now or p.entry_price, p.entry_price, pk)
                        if sell:
                            from .orders import market_sell_package
                            market_sell_package(p.id, pair, p.quantity)
                            log(pair, f"AUTOSPRZEDAŻ: {reason}", "INFO", strategy=strat.name)

                    # BUY wg strategii
                    will_buy, why, mult = strat.should_buy(price_now or 0.0, ref_low, tph, is_downtrend)
                    if will_buy and price_now:
                        risk_scale = max(0.2, min(2.0, (risk_level+1)/5.0))  # 0..10 -> 0.2..2.2 aprox
                        quote_amt = settings.STRAT_BASE_PACKAGE_USD * mult * risk_scale
                        from .orders import market_buy_package
                        try:
                            market_buy_package(pair, quote_amt)
                            log(pair, f"AUTOKUPNO: {why} (qtyUSD={quote_amt:.2f}, risk={risk_level})", "INFO", strategy=strat.name)
                        except Exception as e:
                            log(pair, f"Błąd kupna: {e}", "ERROR", strategy=strat.name)

                    # alerty PnL (na poziomie całej pozycji)
                    s = get_session()
                    open_pkgs = s.query(Package).filter(Package.pair==pair, Package.sold_at.is_(None)).all()
                    s.close()
                    total_qty = sum(p.quantity for p in open_pkgs) if open_pkgs else 0.0
                    if total_qty > 0 and price_now:
                        entry_avg = sum(p.entry_price*p.quantity for p in open_pkgs)/total_qty
                        pnl_usd = (price_now - entry_avg) * total_qty
                        pnl_pct = (price_now - entry_avg) / entry_avg * 100.0 if entry_avg>0 else 0.0
                        log(pair, f"PNL {pnl_usd:.2f} USD ({pnl_pct:.2f}%)", "INFO", pnl_usd=pnl_usd, pnl_percent=pnl_pct, strategy=strat.name)
                        now2 = datetime.utcnow()
                        last = last_alert.get(pair, {})
                        if pnl_pct >= settings.ALERT_PNL_POSITIVE:
                            if 'pos' not in last or (now2 - last['pos']).total_seconds() >= settings.BOT_INTERVAL_SEC:
                                add_alert(pair, pnl_usd, pnl_pct, "positive")
                                last['pos'] = now2
                        if pnl_pct <= settings.ALERT_PNL_NEGATIVE:
                            if 'neg' not in last or (now2 - last['neg']).total_seconds() >= settings.BOT_INTERVAL_SEC:
                                add_alert(pair, pnl_usd, pnl_pct, "negative")
                                last['neg'] = now2
                        last_alert[pair] = last

        await asyncio.sleep(settings.BOT_INTERVAL_SEC)

@app.on_event("startup")
async def on_start():
    asyncio.create_task(loop_task())
