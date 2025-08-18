import os

def getenv_bool(key: str, default: bool=False) -> bool:
    v = os.getenv(key, str(default)).strip().lower()
    return v in ("1","true","yes","y","on")

class Settings:
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY","")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET","")
    BINANCE_TESTNET = getenv_bool("BINANCE_TESTNET", True)
    DEFAULT_PAIRS = [s.strip().upper() for s in os.getenv("DEFAULT_PAIRS","BTCUSDC,ETHUSDC").split(",") if s.strip()]
    ALLOWED_QUOTES = [s.strip().upper() for s in os.getenv("ALLOWED_QUOTES","USDC,BTC,BNB").split(",") if s.strip()]

    DB_HOST = os.getenv("DB_HOST","localhost")
    DB_PORT = int(os.getenv("DB_PORT","3306"))
    DB_NAME = os.getenv("DB_NAME","crypto_bot")
    DB_USER = os.getenv("DB_USER","crypto_bot")
    DB_PASSWORD = os.getenv("DB_PASSWORD","")

    BOT_INTERVAL_SEC = int(os.getenv("BOT_INTERVAL_SEC","300"))
    BASE_CURRENCY = os.getenv("BASE_CURRENCY","PLN")
    SHOW_CHARTS = getenv_bool("SHOW_CHARTS", True)
    AUTO_TRADE = getenv_bool("AUTO_TRADE", False)

    STRAT_MIN_PROFIT_PCT = float(os.getenv("STRAT_MIN_PROFIT_PCT","5.0"))
    STRAT_HYSTERESIS_PCT = float(os.getenv("STRAT_HYSTERESIS_PCT","1.0"))
    STRAT_BUY_DRAWDOWN_PCT = float(os.getenv("STRAT_BUY_DRAWDOWN_PCT","3.0"))
    STRAT_MIN_TRADES_PER_HOUR = int(os.getenv("STRAT_MIN_TRADES_PER_HOUR","100"))
    STRAT_BASE_PACKAGE_USD = float(os.getenv("STRAT_BASE_PACKAGE_USD","50.0"))
    STRAT_DOWNTREND_MULTIPLIER = float(os.getenv("STRAT_DOWNTREND_MULTIPLIER","2.0"))
    STRAT_BUY_LOOKBACK = os.getenv("STRAT_BUY_LOOKBACK","day").lower()

    ALERT_PNL_POSITIVE = float(os.getenv("ALERT_PNL_POSITIVE","10"))
    ALERT_PNL_NEGATIVE = float(os.getenv("ALERT_PNL_NEGATIVE","-5"))

    FX_ENABLED = getenv_bool("FX_ENABLED", True)
    EQUITIES_ENABLED = getenv_bool("EQUITIES_ENABLED", False)

    API_BIND = os.getenv("API_BIND","0.0.0.0")
    API_PORT = int(os.getenv("API_PORT","8080"))

settings = Settings()
