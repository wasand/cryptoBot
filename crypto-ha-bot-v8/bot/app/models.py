from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Integer, String, Text, Boolean, Float, Date
from datetime import datetime
from .database import Base

class MarketData(Base):
    __tablename__ = "market_data"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(36), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    pair: Mapped[str] = mapped_column(String(16), index=True)
    price: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    trades_per_hour: Mapped[int] = mapped_column(Integer, default=0)
    ema_fast: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema_slow: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd: Mapped[float | None] = mapped_column(Float, nullable=True)
    atr: Mapped[float | None] = mapped_column(Float, nullable=True)

class Package(Base):
    __tablename__ = "packages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pair: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    quantity: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    realized_pnl_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl_pln: Mapped[float | None] = mapped_column(Float, nullable=True)

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    pair: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    pnl_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(64), nullable=True)

class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    total_value_pln: Mapped[float] = mapped_column(Float)
    total_value_usd: Mapped[float] = mapped_column(Float)
    realized_pnl_pln: Mapped[float] = mapped_column(Float)
    unrealized_pnl_pln: Mapped[float] = mapped_column(Float)
    realized_pnl_usd: Mapped[float] = mapped_column(Float)
    unrealized_pnl_usd: Mapped[float] = mapped_column(Float)
    strategy_name: Mapped[str | None] = mapped_column(String(64))
    risk_level: Mapped[int | None] = mapped_column(Integer)
    market: Mapped[str | None] = mapped_column(String(16))
    volume_filter: Mapped[int | None] = mapped_column(Integer)

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    pair: Mapped[str] = mapped_column(String(16), index=True)
    pnl_usd: Mapped[float] = mapped_column(Float)
    pnl_percent: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(16))

class PairConfig(Base):
    __tablename__ = "pair_config"
    pair: Mapped[str] = mapped_column(String(16), primary_key=True)
    allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    risk_level: Mapped[int] = mapped_column(Integer, default=5)

class FxRate(Base):
    __tablename__ = "fx_rates"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(36), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    base: Mapped[str] = mapped_column(String(8))
    quote: Mapped[str] = mapped_column(String(8))
    rate: Mapped[float] = mapped_column(Float)

class EquityPrice(Base):
    __tablename__ = "equity_prices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(36), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    price: Mapped[float] = mapped_column(Float)

class StockPortfolio(Base):
    __tablename__ = "stock_portfolios"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(36), index=True)
    fund_name: Mapped[str] = mapped_column(String(100))
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    shares: Mapped[int] = mapped_column(Integer)
    value_usd: Mapped[float] = mapped_column(Float)
    report_date: Mapped[date] = mapped_column(Date)

class MLFeature(Base):
    __tablename__ = "ml_features"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(36), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    feature_name: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(Text)