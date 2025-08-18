from .checks import check_db, check_binance
from .config import settings

def main():
    print("== Checking DB connection ==")
    try:
        check_db()
        print("OK: MariaDB connected")
    except Exception as e:
        print("ERROR: MariaDB", e); return

    print("== Checking Binance (testnet=%s) ==" % settings.BINANCE_TESTNET)
    try:
        n = check_binance()
        print(f"OK: Binance reachable, symbols: {n}")
    except Exception as e:
        print("ERROR: Binance", e); return

    print("== Default pairs ==", settings.DEFAULT_PAIRS)
    print("All good.")

if __name__ == "__main__":
    main()
