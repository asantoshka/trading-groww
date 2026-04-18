import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, model_validator


class TradeResponse(BaseModel):
    id: str
    symbol: str
    exchange: str
    action: str
    qty: int
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    product: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None
    signal_reason: Optional[str] = None
    duration: Optional[str] = None
    entry_time: Optional[str] = None
    exit_time: Optional[str] = None
    created_at: datetime
    date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SignalResponse(BaseModel):
    id: str
    timestamp: str
    symbol: str
    exchange: Optional[str] = None
    action: str
    entry_price: float
    target: float
    stoploss: float
    qty: int
    rsi: Optional[float] = None
    macd_state: Optional[str] = None
    confidence: Optional[int] = None
    risk_status: Optional[str] = None
    reject_reason: Optional[str] = None
    executed: bool
    mode: Optional[str] = None
    trade_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PositionResponse(BaseModel):
    id: str
    symbol: str
    exchange: Optional[str] = None
    qty: int
    entry_price: float
    current_ltp: Optional[float] = None
    target: float
    stoploss: float
    product: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None
    entry_order_id: Optional[str] = None
    gtt_order_id: Optional[str] = None
    signal_id: Optional[str] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentLogResponse(BaseModel):
    id: int
    time: str
    agent: str
    level: str
    msg: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConfigResponse(BaseModel):
    id: int
    capital_limit: float
    max_trade_value: float
    max_loss_per_trade: float
    min_rr_ratio: float
    scan_times: list[str]
    watchlist: list[str]
    mode: str
    rsi_oversold: float
    rsi_overbought: float
    confidence_threshold: int
    default_product_type: str
    auto_squareoff_time: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        if data is None:
            return data

        if not isinstance(data, dict):
            data = {
                "id": getattr(data, "id"),
                "capital_limit": getattr(data, "capital_limit"),
                "max_trade_value": getattr(data, "max_trade_value"),
                "max_loss_per_trade": getattr(data, "max_loss_per_trade"),
                "min_rr_ratio": getattr(data, "min_rr_ratio"),
                "scan_times": getattr(data, "scan_times"),
                "watchlist": getattr(data, "watchlist"),
                "mode": getattr(data, "mode"),
                "rsi_oversold": getattr(data, "rsi_oversold"),
                "rsi_overbought": getattr(data, "rsi_overbought"),
                "confidence_threshold": getattr(data, "confidence_threshold"),
                "default_product_type": getattr(data, "default_product_type"),
                "auto_squareoff_time": getattr(data, "auto_squareoff_time"),
                "updated_at": getattr(data, "updated_at"),
            }

        scan_times = data.get("scan_times")
        watchlist = data.get("watchlist")

        if isinstance(scan_times, str):
            data["scan_times"] = json.loads(scan_times)
        if isinstance(watchlist, str):
            data["watchlist"] = json.loads(watchlist)

        return data


class ConfigUpdate(BaseModel):
    capital_limit: Optional[float] = None
    max_trade_value: Optional[float] = None
    max_loss_per_trade: Optional[float] = None
    min_rr_ratio: Optional[float] = None
    scan_times: Optional[list[str]] = None
    watchlist: Optional[list[str]] = None
    mode: Optional[str] = None
    rsi_oversold: Optional[float] = None
    rsi_overbought: Optional[float] = None
    confidence_threshold: Optional[int] = None
    default_product_type: Optional[str] = None
    auto_squareoff_time: Optional[str] = None


class ManualSignalRequest(BaseModel):
    symbol: str
    action: str
    entry_price: float
    target: float
    stoploss: float
    qty: int


class PositionCloseResponse(BaseModel):
    message: str
    position_id: str
    symbol: str
    mode: str

    model_config = ConfigDict(from_attributes=True)
