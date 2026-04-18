import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(String(36), primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(10), nullable=False, default="NSE")
    action = Column(String(10), nullable=False)
    qty = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    product = Column(String(10), default="MIS")
    mode = Column(String(10), default="paper")
    status = Column(String(20), default="open")
    signal_reason = Column(String(500), nullable=True)
    duration = Column(String(50), nullable=True)
    entry_time = Column(String(30), nullable=True)
    exit_time = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    date = Column(String(20), nullable=True)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String(36), primary_key=True, index=True)
    timestamp = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(10), default="NSE")
    action = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    target = Column(Float, nullable=False)
    stoploss = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    rsi = Column(Float, nullable=True)
    macd_state = Column(String(50), nullable=True)
    confidence = Column(Integer, nullable=True)
    risk_status = Column(String(20), default="pending")
    reject_reason = Column(String(500), nullable=True)
    executed = Column(Boolean, default=False)
    mode = Column(String(10), default="paper")
    trade_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(String(20), nullable=False)
    agent = Column(String(50), nullable=False)
    level = Column(String(20), nullable=False)
    msg = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Position(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(10), default="NSE")
    action = Column(String(10), default="BUY")
    qty = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_ltp = Column(Float, nullable=True)
    target = Column(Float, nullable=False)
    stoploss = Column(Float, nullable=False)
    product = Column(String(10), default="MIS")
    mode = Column(String(10), default="paper")
    status = Column(String(20), default="open")
    entry_order_id = Column(String(100), nullable=True)
    gtt_order_id = Column(String(100), nullable=True)
    signal_id = Column(String(36), nullable=True)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    entry_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    capital_limit = Column(Float, default=5000.0)
    max_trade_value = Column(Float, default=2000.0)
    max_loss_per_trade = Column(Float, default=300.0)
    min_rr_ratio = Column(Float, default=1.5)
    scan_times = Column(String(200), default='["09:15","11:00","13:30"]')
    watchlist = Column(
        String(500),
        default='["NHPC","SAIL","NBCC","IRFC","HUDCO","RVNL","BHEL","NTPC","POWERGRID","RECLTD","PFC","SJVN","NMDC","NATIONALUM","MRPL","HINDPETRO","BANKBARODA","CANBK","IDEA","SUZLON"]',
    )
    mode = Column(String(10), default="paper")
    rsi_oversold = Column(Float, default=35.0)
    rsi_overbought = Column(Float, default=65.0)
    confidence_threshold = Column(Integer, default=70)
    default_product_type = Column(String(10), default="MIS")
    auto_squareoff_time = Column(String(10), default="15:15")
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def get_scan_times(self) -> list[str]:
        return json.loads(self.scan_times or "[]")

    def get_watchlist(self) -> list[str]:
        return json.loads(self.watchlist or "[]")
