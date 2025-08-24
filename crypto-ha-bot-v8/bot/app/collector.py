from .binance_client import get_client
from .database import get_session
from .models import MarketData
from datetime import datetime
from .config import settings
from sqlalchemy import insert
import uuid

def fetch_and_store_pairs(pairs, batch_id):
    client = get_client()
    with get_session() as session:
        for pair in pairs:
            try:
                ticker = client.ticker_24hr(symbol=pair)  # Używamy ticker_24hr dla volume i count
                session.execute(
                    insert(MarketData),
                    {
                        "batch_id": batch_id,
                        "ts": datetime.utcnow(),  # Używamy UTC dla spójności
                        "pair": pair,
                        "price": float(ticker["lastPrice"]),
                        "volume": float(ticker["volume"]),
                        "trades_per_hour": int(ticker["count"]) / 24,  # Obliczamy trades_per_hour
                        "ema_fast": 0.0,
                        "ema_slow": 0.0,
                        "macd": 0.0,
                        "atr": 0.0
                    }
                )
                session.commit()
                print(f"Stored data for {pair}: price={ticker['lastPrice']}, volume={ticker['volume']}, trades_per_hour={int(ticker['count']) / 24}")
            except Exception as e:
                print(f"Error fetching/storing data for {pair}: {e}")

async def fetch_data_cycle():
    batch_id = str(uuid.uuid4())
    pairs = settings.DEFAULT_PAIRS
    print(f"Starting fetch_data_cycle with pairs: {pairs}")
    fetch_and_store_pairs(pairs, batch_id)
    print("Completed fetch_data_cycle")
