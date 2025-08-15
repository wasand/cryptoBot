from .config import settings
from .database import engine
from .binance_client import get_client
from sqlalchemy import text

def main():
    print("== Checking DB connection ==")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("OK: MariaDB connected")
    except Exception as e:
        print("ERROR: MariaDB", e); return

    print("== Checking Binance Testnet ==")
    try:
        client = get_client()
        exch = client.exchange_info()
        print("OK: Binance reachable, symbols:", len(exch.get("symbols", [])))
    except Exception as e:
        print("ERROR: Binance", e); return

    print("== Default pairs ==", settings.DEFAULT_PAIRS)
    print("All good.")

if __name__ == "__main__":
    main()
