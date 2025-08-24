import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

# Load .env file
load_dotenv()

# Settings from .env
DB_HOST = os.getenv("DB_HOST", "addon_core_mariadb")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "crypto_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "crypto_bot")

# Connect to the database
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?ssl_disabled=true")
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# List of expected tables
expected_tables = [
    "alerts", "equity_prices", "fx_rates", "market_data", "ml_features",
    "packages", "pair_config", "portfolio_history", "stock_portfolios", "trade_logs"
]

# Check and create tables if missing
for table in expected_tables:
    try:
        session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
        print(f"Table {table} exists and is accessible.")
    except OperationalError as e:
        if table in str(e):
            print(f"Table {table} does not exist. Creating...")
            if table == "market_data":
                session.execute(text("""
                    CREATE TABLE market_data (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        batch_id VARCHAR(36),
                        ts DATETIME,
                        pair VARCHAR(16),
                        price FLOAT,
                        volume FLOAT,
                        trades_per_hour INT,
                        ema_fast FLOAT,
                        ema_slow FLOAT,
                        macd FLOAT,
                        atr FLOAT
                    )
                """))
            elif table == "pair_config":
                session.execute(text("""
                    CREATE TABLE pair_config (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        pair VARCHAR(16) UNIQUE,
                        allowed BOOLEAN,
                        risk_level INT
                    )
                """))
            # Add definitions for other tables if needed
            session.commit()
            print(f"Table {table} created.")
        else:
            print(f"Error accessing table {table}: {e}")
session.close()
