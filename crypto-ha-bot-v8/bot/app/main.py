import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from .config import settings
from .database import engine, Base, get_session
from .models import MarketData, Package, TradeLog, Alert, PairConfig
from .collector import fetch_data_cycle
from .strategies import SimpleStrategy, StrategyParams
from .logger import log, add_alert
from .pnl import latest_price, last_points, peak_since, last_tph, latest_fx_rate
from .checks import is_quote_allowed
from .orders import market_buy_package, market_sell_package
import uuid

app = FastAPI(title="Crypto HA Bot v8.5", version="8.5")

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

class StartBody(BaseModel):
    pairs: list[str] | None = None
    autotrade: bool | None = None

class BuyBody(BaseModel):
    pair: str
    quote_amount_usd: float

class SellBody(BaseModel):
    pair: str
    package_id: int | None = None

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
def buy(body: BuyBody):
    if not is_quote_allowed(body.pair):
        raise HTTPException(400, "Invalid pair")
    return market_buy_package(body.pair, body.quote_amount_usd)

@app.post("/order/sell")
def sell(body: SellBody):
    if not is_quote_allowed(body.pair):
        raise HTTPException(400, "Invalid pair")
    s = get_session()
    if body.package_id:
        pkg = s.query(Package).filter(Package.id==body.package_id).first()
        if not pkg or pkg.sold_at:
            s.close()
            raise HTTPException(400, "Invalid or sold package")
        result = market_sell_package(body.package_id, body.pair, pkg.quantity)
    else:
        pkgs = s.query(Package).filter(Package.pair==body.pair, Package.sold_at.is_(None)).all()
        result = []
        for pkg in pkgs:
            result.append(market_sell_package(pkg.id, body.pair, pkg.quantity))
    s.close()
    return result

@app.get("/config")
def get_config():
    return {
        "min_profit_pct": settings.STRAT_MIN_PROFIT_PCT,
        "hysteresis_pct": settings.STRAT_HYSTERESIS_PCT,
        "buy_drawdown_pct": settings.STRAT_BUY_DRAWDOWN_PCT,
        "min_trades_per_hour": settings.STRAT_MIN_TRADES_PER_HOUR,
        "base_package_usd": settings.STRAT_BASE_PACKAGE_USD,
        "downtrend_multiplier": settings.STRAT_DOWNTREND_MULTIPLIER,
        "buy_lookback": settings.STRAT_BUY_LOOKBACK
    }

@app.put("/config")
def update_config(body: ConfigBody):
    if body.min_profit_pct is not None:
        settings.STRAT_MIN_PROFIT_PCT = body.min_profit_pct
    if body.hysteresis_pct is not None:
        settings.STRAT_HYSTERESIS_PCT = body.hysteresis_pct
    if body.buy_drawdown_pct is not None:
        settings.STRAT_BUY_DRAWDOWN_PCT = body.buy_drawdown_pct
    if body.min_trades_per_hour is not None:
        settings.STRAT_MIN_TRADES_PER_HOUR = body.min_trades_per_hour
    if body.base_package_usd is not None:
        settings.STRAT_BASE_PACKAGE_USD = body.base_package_usd
    if body.downtrend_multiplier is not None:
        settings.STRAT_DOWNTREND_MULTIPLIER = body.downtrend_multiplier
    if body.buy_lookback is not None:
        settings.STRAT_BUY_LOOKBACK = body.buy_lookback
    return get_config()

@app.get("/pair-config")
def get_pair_config():
    s = get_session()
    configs = s.query(PairConfig).all()
    s.close()
    return [{"pair": c.pair, "allowed": c.allowed, "risk_level": c.risk_level} for c in configs]

@app.put("/pair-config")
def update_pair_config(body: PairCfgBody):
    s = get_session()
    cfg = s.query(PairConfig).filter(PairConfig.pair==body.pair).first()
    if not cfg:
        cfg = PairConfig(pair=body.pair)
        s.add(cfg)
    if body.allowed is not None:
        cfg.allowed = body.allowed
    if body.risk_level is not None:
        cfg.risk_level = max(0, min(10, body.risk_level))
    s.commit(); s.close()
    return {"pair": cfg.pair, "allowed": cfg.allowed, "risk_level": cfg.risk_level}

@app.get("/logs")
def get_logs(limit: int = 50):
    s = get_session()
    logs = s.query(TradeLog).order_by(TradeLog.ts.desc()).limit(limit).all()
    s.close()
    return [{"ts": l.ts.isoformat(), "pair": l.pair, "level": l.level, "message": l.message, "pnl_usd": l.pnl_usd, "pnl_percent": l.pnl_percent, "strategy": l.strategy} for l in logs]

@app.get("/alerts")
def get_alerts(limit: int = 50):
    s = get_session()
    alerts = s.query(Alert).order_by(Alert.ts.desc()).limit(limit).all()
    s.close()
    return [{"ts": a.ts.isoformat(), "pair": a.pair, "type": a.type, "pnl_usd": a.pnl_usd, "pnl_percent": a.pnl_percent} for a in alerts]

@app.delete("/alerts")
def clear_alerts():
    s = get_session()
    s.query(Alert).delete()
    s.commit(); s.close()
    return {"status": "ok"}

@app.get("/market/history")
def market_history(pair: str, limit: int = 100):
    if not is_quote_allowed(pair):
        raise HTTPException(400, "Invalid pair")
    points = last_points(pair, limit)
    return {"pair": pair, "points": points}

async def loop_task():
    global running, autotrade, last_alert
    strat = SimpleStrategy(StrategyParams(
        min_profit_pct=settings.STRAT_MIN_PROFIT_PCT,
        hysteresis_pct=settings.STRAT_HYSTERESIS_PCT,
        buy_drawdown_pct=settings.STRAT_BUY_DRAWDOWN_PCT,
        min_trades_per_hour=settings.STRAT_MIN_TRADES_PER_HOUR,
        base_package_usd=settings.STRAT_BASE_PACKAGE_USD,
        downtrend_multiplier=settings.STRAT_DOWNTREND_MULTIPLIER,
        buy_lookback=settings.STRAT_BUY_LOOKBACK
    ))
    while True:
        if running:
            fetch_data_cycle()
            if autotrade:
                s = get_session()
                pairs = s.query(PairConfig).filter(PairConfig.allowed==True).all()
                s.close()
                for cfg in pairs:
                    pair = cfg.pair
                    risk_level = cfg.risk_level
                    price_now = latest_price(pair)
                    tph = last_tph(pair)
                    since = {"day": 1, "week": 7, "month": 30}.get(settings.STRAT_BUY_LOOKBACK, 1)
                    ref_low = peak_since(pair, datetime.utcnow() - timedelta(days=since))
                    is_downtrend = price_now and ref_low and price_now < ref_low
                    will_buy, why, mult = strat.should_buy(pair, price_now or 0.0, ref_low or 0.0, tph, is_downtrend)
                    if will_buy and price_now:
                        risk_scale = max(0.2, min(2.0, (risk_level+1)/5.0))
                        quote_amt = settings.STRAT_BASE_PACKAGE_USD * mult * risk_scale
                        try:
                            market_buy_package(pair, quote_amt)
                            log(pair, f"AUTOKUPNO: {why} (qtyUSD={quote_amt:.2f}, risk={risk_level})", "INFO", strategy=strat.name)
                        except Exception as e:
                            log(pair, f"Błąd kupna: {e}", "ERROR", strategy=strat.name)
                    s = get_session()
                    open_pkgs = s.query(Package).filter(Package.pair==pair, Package.sold_at.is_(None)).all()
                    s.close()
                    total_qty = sum(p.quantity for p in open_pkgs) if open_pkgs else 0.0
                    if total_qty > 0 and price_now:
                        entry_avg = sum(p.entry_price*p.quantity for p in open_pkgs)/total_qty
                        pnl_usd = (price_now - entry_avg) * total_qty
                        pnl_pct = (price_now - entry_avg) / entry_avg * 100.0 if entry_avg > 0 else 0.0
                        log(pair, f"PNL {pnl_usd:.2f} USD ({pnl_pct:.2f}%)", "INFO", pnl_usd=pnl_usd, pnl_percent=pnl_pct, strategy=strat.name)
                        now = datetime.utcnow()
                        last = last_alert.get(pair, {})
                        if pnl_pct >= settings.ALERT_PNL_POSITIVE:
                            if 'pos' not in last or (now - last['pos']).total_seconds() >= settings.BOT_INTERVAL_SEC:
                                add_alert(pair, pnl_usd, pnl_pct, "positive")
                                last['pos'] = now
                        if pnl_pct <= settings.ALERT_PNL_NEGATIVE:
                            if 'neg' not in last or (now - last['neg']).total_seconds() >= settings.BOT_INTERVAL_SEC:
                                add_alert(pair, pnl_usd, pnl_pct, "negative")
                                last['neg'] = now
                        last_alert[pair] = last
        await asyncio.sleep(settings.BOT_INTERVAL_SEC)

@app.on_event("startup")
async def on_start():
    asyncio.create_task(loop_task())