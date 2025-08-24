from .binance_client import get_client
from .database import get_session
from .models import FXRate
from datetime import datetime
from .config import settings
from sqlalchemy import insert
import asyncio

async def fetch_fx_cycle():
    client = get_client()
    fx_pairs = getattr(settings, 'FX_PAIRS', ['USDEUR', 'USDJPY'])  # Domyślne pary, jeśli nie zdefiniowane
    print(f"Starting fx_collector with pairs: {fx_pairs}")
    with get_session() as session:
        for pair in fx_pairs:
            try:
                ticker = client.ticker_price(symbol=pair)
                base, quote = pair[:3], pair[3:]  # Rozdzielamy np. USDEUR na USD i EUR
                session.execute(
                    insert(FXRate),
                    {
                        "ts": datetime.utcnow(),
                        "base": base,
                        "quote": quote,
                        "rate": float(ticker["price"])
                    }
                )
                session.commit()
                print(f"Stored FX rate for {pair}: rate={ticker['price']}")
            except Exception as e:
                print(f"Error fetching/storing FX rate for {pair}: {e}")
    print("Completed fx_collector cycle")

async def fx_loop():
    print("Starting FX collector loop")
    while True:
        await fetch_fx_cycle()
        print(f"Sleeping for {getattr(settings, 'FX_INTERVAL_SEC', 60)} seconds")
        await asyncio.sleep(getattr(settings, 'FX_INTERVAL_SEC', 60))

if __name__ == "__main__":
    asyncio.run(fx_loop())
