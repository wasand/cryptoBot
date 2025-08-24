from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from .database import Base

class FXRate(Base):
    __tablename__ = "fx_rates"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ts = Column(DateTime, nullable=False)
    base = Column(String(8), nullable=False)
    quote = Column(String(8), nullable=False)
    rate = Column(Float, nullable=False)

class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(36))
    ts = Column(DateTime)
    pair = Column(String(16))
    price = Column(Float)
    volume = Column(Float)
    trades_per_hour = Column(Integer)
    ema_fast = Column(Float, nullable=True)
    ema_slow = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)

class Package(Base):
    __tablename__ = "packages"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(16), index=True)
    created_at = Column(DateTime)
    quantity = Column(Float)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    bought_at = Column(DateTime, nullable=True)
    sold_at = Column(DateTime, nullable=True)
    realized_pnl_usd = Column(Float, nullable=True)
    realized_pnl_pln = Column(Float, nullable=True)

class TradeLog(Base):
    __tablename__ = "trade_logs"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, index=True)
    pair = Column(String(16))
    level = Column(String(16))
    message = Column(String)
    pnl_usd = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    strategy = Column(String(32), nullable=True)

class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime)
    pair = Column(String(16))
    pnl_usd = Column(Float)
    pnl_percent = Column(Float)
    type = Column(String(16))

class PairConfig(Base):
    __tablename__ = "pair_config"
    __table_args__ = {'extend_existing': True}
    pair = Column(String(16), primary_key=True)
    allowed = Column(Boolean)
    risk_level = Column(Integer)

class EquityPrice(Base):
    __tablename__ = "equity_prices"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime)
    symbol = Column(String(16))
    price = Column(Float)

class MLFeature(Base):
    __tablename__ = "ml_features"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, index=True)
    batch_id = Column(String(36), index=True)
    feature_name = Column(String(32))
    value = Column(String)

class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, index=True)
    equity_usd = Column(Float)
    total_pnl_usd = Column(Float)
    total_pnl_percent = Column(Float)

class StockPortfolio(Base):
    __tablename__ = "stock_portfolios"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(36), index=True)
    symbol = Column(String(16), index=True)
    quantity = Column(Float)
    avg_price = Column(Float)
