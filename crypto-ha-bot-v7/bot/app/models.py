from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Integer, String, Text
from datetime import datetime
from .database import Base

class MarketData(Base):
    __tablename__ = "market_data"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    pair: Mapped[str] = mapped_column(String(16), index=True)
    price: Mapped[str] = mapped_column(String(64))
    volume: Mapped[str] = mapped_column(String(64))
    trades_per_hour: Mapped[int] = mapped_column(Integer, default=0)

class Package(Base):
    __tablename__ = "packages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pair: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    quantity: Mapped[str] = mapped_column(String(64))
    entry_price: Mapped[str] = mapped_column(String(64))
    exit_price: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    realized_pnl_usd: Mapped[str | None] = mapped_column(String(64), nullable=True)
    realized_pnl_pln: Mapped[str | None] = mapped_column(String(64), nullable=True)

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    pair: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    pnl_usd: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pnl_percent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(64), nullable=True)

class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    total_value_pln: Mapped[str] = mapped_column(String(64))
    total_value_usd: Mapped[str] = mapped_column(String(64))
    realized_pnl_pln: Mapped[str] = mapped_column(String(64))
    unrealized_pnl_pln: Mapped[str] = mapped_column(String(64))
    realized_pnl_usd: Mapped[str] = mapped_column(String(64))
    unrealized_pnl_usd: Mapped[str] = mapped_column(String(64))
    strategy_name: Mapped[str | None] = mapped_column(String(64))
    risk_level: Mapped[int | None] = mapped_column(Integer)
    market: Mapped[str | None] = mapped_column(String(16))
    volume_filter: Mapped[int | None] = mapped_column(Integer)

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    pair: Mapped[str] = mapped_column(String(16), index=True)
    pnl_usd: Mapped[str] = mapped_column(String(64))
    pnl_percent: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(16))  # positive/negative
