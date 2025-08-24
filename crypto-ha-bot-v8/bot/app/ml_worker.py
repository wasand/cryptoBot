import asyncio
import numpy as np
import pandas as pd
from datetime import datetime
from .database import get_session
from .config import settings
from .models import MarketData, MLFeature
from sqlalchemy import select, insert
from statsmodels.tsa.stattools import grangercausalitytests
import uuid

async def compute_features():
    with get_session() as session:
        for pair in settings.DEFAULT_PAIRS:
            # Pobierz dane tylko dla danej pary
            result = session.execute(
                select(MarketData).where(MarketData.pair == pair).order_by(MarketData.ts.desc()).limit(50)
            ).scalars().all()
            if len(result) < 11:
                print(f"Not enough data for {pair} in market_data ({len(result)} rows), need at least 10 rows")
                continue

            df = pd.DataFrame([{
                "ts": r.ts,
                "price": r.price,
                "volume": r.volume,
                "trades_per_hour": r.trades_per_hour
            } for r in result])

            if df["volume"].nunique() <= 1:
                print(f"Volume is constant or missing for {pair} ({df['volume'].nunique()} unique values), skipping Granger test")
                continue

            try:
                # Test Granger Causality dla ceny i wolumenu
                data = df[["price", "volume"]].dropna()
                maxlag = min(3, len(data) - 2)  # Ogranicz maxlag
                if maxlag <= 0:
                    print(f"Insufficient observations for {pair}. Maximum allowable lag is 0")
                    continue
                gc_results = grangercausalitytests(data, maxlag=maxlag, verbose=False)

                # Zapisz wyniki do ml_features
                batch_id = str(uuid.uuid4())
                session.execute(
                    insert(MLFeature),
                    {
                        "batch_id": batch_id,
                        "ts": datetime.utcnow(),  # Dodajemy timestamp
                        "feature_name": "granger_causality",
                        "value": str(gc_results)
                    }
                )
                session.commit()
                print(f"Computed and stored Granger Causality for {pair}")
            except Exception as e:
                print(f"ML error for {pair}: {e}")

async def ml_loop():
    print("Starting ML worker loop")
    while True:
        await compute_features()
        print(f"Sleeping for {settings.FX_INTERVAL_SEC} seconds")
        await asyncio.sleep(settings.FX_INTERVAL_SEC)

if __name__ == "__main__":
    asyncio.run(ml_loop())
