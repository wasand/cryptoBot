import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from .config import settings
from .database import engine, Base, get_session
from .models import MarketData, Package, TradeLog, PortfolioHistory, Alert
from .collector import fetch_and_store_pairs
from .strategies import SimpleStrategy, StrategyParams
from .logger import log, add_alert
from .pnl import latest_price

app = FastAPI(title="Crypto HA Bot v7", version="7.0")
Base.metadata.create_all(bind=engine)

running = False
last_alert = {}  # pair -> { 'pos': ts, 'neg': ts }

class StartBody(BaseModel):
    pairs: list[str] | None = None

@app.get("/health")
def health():
    return {"status":"ok","running":running, "pairs": settings.DEFAULT_PAIRS}

@app.post("/start")
def start_bot(body: StartBody | None=None):
    global running
    running = True
    if body and body.pairs:
        settings.DEFAULT_PAIRS = [p.upper() for p in body.pairs]
    return {"running": running, "pairs": settings.DEFAULT_PAIRS}

@app.post("/stop")
def stop_bot():
    global running
    running = False
    return {"running": running}

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

async def loop_task():
    params = StrategyParams()
    strat = SimpleStrategy(params)

    while True:
        if running:
            fetch_and_store_pairs(settings.DEFAULT_PAIRS)

            for pair in settings.DEFAULT_PAIRS:
                price_now = latest_price(pair)
                if price_now is None:
                    continue

                s = get_session()
                open_pkgs = s.query(Package).filter(Package.pair==pair, Package.sold_at.is_(None)).all()
                s.close()

                total_qty = sum(float(p.quantity) for p in open_pkgs) if open_pkgs else 0.0
                if total_qty > 0:
                    entry_avg = sum(float(p.entry_price)*float(p.quantity) for p in open_pkgs)/total_qty
                    pnl_usd = (price_now - entry_avg) * total_qty
                    pnl_pct = (price_now - entry_avg) / entry_avg * 100.0 if entry_avg>0 else 0.0
                    log(pair, f"PNL {pnl_usd:.2f} USD ({pnl_pct:.2f}%)", "INFO", pnl_usd=pnl_usd, pnl_percent=pnl_pct, strategy=strat.name)

                    now = datetime.utcnow()
                    last = last_alert.get(pair, {})
                    if pnl_pct >= settings.ALERT_PNL_POSITIVE:
                        if 'pos' not in last:
                            add_alert(pair, pnl_usd, pnl_pct, "positive")
                            last['pos'] = now
                    if pnl_pct <= settings.ALERT_PNL_NEGATIVE:
                        if 'neg' not in last:
                            add_alert(pair, pnl_usd, pnl_pct, "negative")
                            last['neg'] = now
                    last_alert[pair] = last
                else:
                    log(pair, "Brak otwartych pakietów - tylko monitoring", "DEBUG", strategy=strat.name)

        await asyncio.sleep(settings.BOT_INTERVAL_SEC)

@app.on_event("startup")
async def on_start():
    asyncio.create_task(loop_task())
