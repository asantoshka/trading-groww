import json
import uuid
from datetime import datetime, timezone

import mock_data
import models
from database import Base, SessionLocal, engine


def seed_config(session) -> None:
    config = session.query(models.Config).filter(models.Config.id == 1).first()
    if config:
        print("Config already seeded. Skipping.")
        return

    config = models.Config(
        id=1,
        capital_limit=mock_data.MOCK_CONFIG["capital_limit"],
        max_trade_value=mock_data.MOCK_CONFIG["max_trade_value"],
        max_loss_per_trade=mock_data.MOCK_CONFIG["max_loss_per_trade"],
        min_rr_ratio=mock_data.MOCK_CONFIG["min_rr_ratio"],
        scan_times=json.dumps(mock_data.MOCK_CONFIG["scan_times"]),
        watchlist=json.dumps(mock_data.MOCK_CONFIG["watchlist"]),
        mode=mock_data.MOCK_CONFIG["mode"],
        rsi_oversold=mock_data.MOCK_CONFIG["rsi_oversold"],
        rsi_overbought=mock_data.MOCK_CONFIG["rsi_overbought"],
        confidence_threshold=mock_data.MOCK_CONFIG["confidence_threshold"],
        default_product_type=mock_data.MOCK_CONFIG["default_product_type"],
        auto_squareoff_time=mock_data.MOCK_CONFIG["auto_squareoff_time"],
        updated_at=datetime.now(timezone.utc),
    )
    session.add(config)
    print("Seeded config table.")


def seed_trades(session) -> None:
    if session.query(models.Trade).count() > 0:
        print("Trades already seeded. Skipping.")
        return

    for item in mock_data.MOCK_TRADES:
        trade = models.Trade(
            id=item.get("id") or str(uuid.uuid4()),
            symbol=item["symbol"],
            exchange=item.get("exchange", "NSE"),
            action=item["action"],
            qty=item["qty"],
            entry_price=item["entry_price"],
            exit_price=item.get("exit_price"),
            pnl=item.get("pnl"),
            pnl_pct=item.get("pnl_pct"),
            product=item.get("product", "MIS"),
            mode=item.get("mode", "paper"),
            status=item.get("status", "open"),
            signal_reason=item.get("signal_reason"),
            duration=item.get("duration"),
            entry_time=item.get("entry_time"),
            exit_time=item.get("exit_time"),
            date=item.get("date"),
        )
        session.add(trade)

    print("Seeded trades table.")


def seed_signals(session) -> None:
    if session.query(models.Signal).count() > 0:
        print("Signals already seeded. Skipping.")
        return

    for item in mock_data.MOCK_SIGNALS:
        signal = models.Signal(
            id=item.get("id") or str(uuid.uuid4()),
            timestamp=item["timestamp"],
            symbol=item["symbol"],
            exchange=item.get("exchange", "NSE"),
            action=item["action"],
            entry_price=item["entry_price"],
            target=item["target"],
            stoploss=item["stoploss"],
            qty=item["qty"],
            rsi=item.get("rsi"),
            macd_state=item.get("macd_state"),
            confidence=item.get("confidence"),
            risk_status=item.get("risk_status", "pending"),
            reject_reason=item.get("reject_reason"),
            executed=item.get("executed", False),
            mode=item.get("mode", "paper"),
            trade_id=item.get("trade_id"),
        )
        session.add(signal)

    print("Seeded signals table.")


def seed_agent_logs(session) -> None:
    if session.query(models.AgentLog).count() > 0:
        print("Agent logs already seeded. Skipping.")
        return

    for item in mock_data.MOCK_AGENT_LOGS:
        log = models.AgentLog(
            time=item["time"],
            agent=item["agent"],
            level=item["level"],
            msg=item["msg"],
        )
        session.add(log)

    print("Seeded agent_logs table.")


def main() -> None:
    import sys

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        if "--config-only" in sys.argv:
            seed_config(session)
            session.commit()
            print("Config-only seed complete")
        else:
            seed_config(session)
            seed_trades(session)
            seed_signals(session)
            seed_agent_logs(session)
            session.commit()
            print("Seed complete. DB ready.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
