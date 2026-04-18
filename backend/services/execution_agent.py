import asyncio
import logging
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Config, Position, Signal, Trade
from services.groww_client import groww_client
from services.market_hours import is_entry_allowed
from services.telegram_notifier import telegram
from services.websocket_manager import (
    broadcast_agent_log,
    broadcast_agent_status,
    broadcast_ltp_update,
    broadcast_order_filled,
    broadcast_pnl_update,
)


logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
SQUAREOFF_HOUR_IST = 15
SQUAREOFF_MINUTE_IST = 10


class ExecutionAgent:
    def __init__(self):
        self.is_running = False
        self._active_positions: dict[str, dict] = {}
        self._monitoring_task = None
        self._last_order: dict | None = None

    async def _place_entry_order(
        self,
        signal: Signal,
        db: Session,
    ) -> dict | None:
        _ = db
        await broadcast_agent_log(
            "execution",
            "info",
            f"Placing LIMIT {signal.action} order: "
            f"{signal.qty} {signal.symbol} "
            f"@ ₹{signal.entry_price}",
        )

        try:
            order = await groww_client.place_order(
                symbol=signal.symbol,
                qty=signal.qty,
                price=signal.entry_price,
                action=signal.action,
                product="MIS",
                order_type="LIMIT",
            )
        except Exception as exc:
            await broadcast_agent_log(
                "execution",
                "error",
                f"Order placement failed: {str(exc)}",
            )
            return None

        await broadcast_agent_log(
            "execution",
            "success",
            f"Order placed: {signal.action} "
            f"{signal.qty} {signal.symbol} "
            f"@ ₹{signal.entry_price} | "
            f"ID: {order['groww_order_id']}",
        )
        await telegram.notify_order_placed(
            symbol=signal.symbol,
            action=signal.action,
            qty=signal.qty,
            price=signal.entry_price,
            order_id=order["groww_order_id"],
            mode=signal.mode,
        )
        return order

    async def _place_gtt_stoploss(
        self,
        signal: Signal,
        entry_order_id: str,
    ) -> dict | None:
        _ = entry_order_id
        await broadcast_agent_log(
            "execution",
            "info",
            f"Placing GTT stoploss: SELL "
            f"{signal.qty} {signal.symbol} "
            f"if price <= ₹{signal.stoploss}",
        )

        try:
            gtt = await groww_client.place_gtt_stoploss(
                symbol=signal.symbol,
                qty=signal.qty,
                stoploss=signal.stoploss,
                product="MIS",
                position_action=signal.action,
            )
        except Exception as exc:
            await broadcast_agent_log(
                "execution",
                "warning",
                f"GTT stoploss failed (manual SL needed): {str(exc)}",
            )
            return None

        await broadcast_agent_log(
            "execution",
            "success",
            f"GTT stoploss active: "
            f"trigger @ ₹{signal.stoploss} | "
            f"ID: {gtt['smart_order_id']}",
        )
        await telegram.notify_gtt_placed(
            symbol=signal.symbol,
            qty=signal.qty,
            stoploss=signal.stoploss,
            gtt_id=gtt["smart_order_id"],
        )
        return gtt

    async def _create_position(
        self,
        signal: Signal,
        entry_order: dict,
        gtt_order: dict | None,
        db: Session,
    ) -> Position:
        position = Position(
            id=str(uuid.uuid4()),
            symbol=signal.symbol,
            exchange="NSE",
            action=signal.action,
            qty=signal.qty,
            entry_price=signal.entry_price,
            current_ltp=signal.entry_price,
            target=signal.target,
            stoploss=signal.stoploss,
            product="MIS",
            mode=signal.mode,
            status="open",
            entry_order_id=entry_order["groww_order_id"],
            gtt_order_id=gtt_order["smart_order_id"] if gtt_order else None,
            signal_id=signal.id,
            pnl=0.0,
            pnl_pct=0.0,
            entry_time=datetime.now(timezone.utc),
        )
        db.add(position)
        signal.executed = True
        db.commit()
        db.refresh(position)

        self._active_positions[position.id] = {
            "id": position.id,
            "symbol": position.symbol,
            "qty": position.qty,
            "entry_price": position.entry_price,
            "target": position.target,
            "stoploss": position.stoploss,
            "gtt_order_id": position.gtt_order_id,
            "mode": position.mode,
            "action": signal.action,
            "status": "open",
            "current_ltp": position.current_ltp,
        }

        await broadcast_order_filled(
            order_id=entry_order["groww_order_id"],
            symbol=signal.symbol,
            qty=signal.qty,
            price=signal.entry_price,
            action=signal.action,
            mode=signal.mode,
        )
        return position

    async def _close_position(
        self,
        position_id: str,
        exit_price: float,
        exit_reason: str,
        db: Session,
    ) -> bool:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            return False

        action = position.action or "BUY"
        if action == "BUY":
            pnl = (exit_price - position.entry_price) * position.qty
        else:
            pnl = (position.entry_price - exit_price) * position.qty
        pnl_pct = (pnl / (position.entry_price * position.qty)) * 100

        position.status = "closed"
        position.exit_price = exit_price
        position.exit_time = datetime.now(timezone.utc)
        position.exit_reason = exit_reason
        position.pnl = round(pnl, 2)
        position.pnl_pct = round(pnl_pct, 2)
        position.current_ltp = exit_price

        trade = Trade(
            id=str(uuid.uuid4()),
            symbol=position.symbol,
            exchange=position.exchange,
            action=action,
            qty=position.qty,
            entry_price=position.entry_price,
            exit_price=exit_price,
            pnl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 2),
            product=position.product,
            mode=position.mode,
            status="closed",
            signal_reason=exit_reason,
            entry_time=position.entry_time.strftime("%H:%M:%S")
            if position.entry_time
            else None,
            exit_time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            created_at=datetime.now(timezone.utc),
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        db.add(trade)
        db.commit()

        if exit_reason == "target_hit":
            await telegram.notify_target_hit(
                symbol=position.symbol,
                qty=position.qty,
                entry=position.entry_price,
                exit_price=exit_price,
                pnl=pnl,
                pnl_pct=pnl_pct,
                mode=position.mode,
                action=action,
            )
        elif exit_reason == "stoploss_hit":
            await telegram.notify_stoploss_hit(
                symbol=position.symbol,
                qty=position.qty,
                entry=position.entry_price,
                exit_price=exit_price,
                pnl=pnl,
                pnl_pct=pnl_pct,
                mode=position.mode,
            )

        self._active_positions.pop(position_id, None)

        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        await broadcast_agent_log(
            "execution",
            "success" if pnl >= 0 else "warning",
            f"{pnl_emoji} Position closed: "
            f"{position.symbol} | "
            f"Exit: ₹{exit_price} | "
            f"P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%) | "
            f"Reason: {exit_reason}",
        )

        remaining = db.query(Position).filter(Position.status == "open").all()
        total_pnl = sum(p.pnl or 0 for p in remaining)
        await broadcast_pnl_update(
            total_pnl=total_pnl,
            total_pnl_pct=0.0,
            available_capital=5000.0,
        )
        return True

    async def _check_target_hit(
        self,
        position: dict,
        ltp: float,
    ) -> bool:
        action = position.get("action", "BUY")
        if action == "BUY":
            target_hit = ltp >= position["target"]
            exit_action = "SELL"
            comparator = "≥"
        else:
            target_hit = ltp <= position["target"]
            exit_action = "BUY"
            comparator = "≤"

        if not target_hit:
            return False

        await broadcast_agent_log(
            "execution",
            "success",
            f"🎯 Target hit: {position['symbol']} "
            f"LTP ₹{ltp} {comparator} Target ₹{position['target']}",
        )

        try:
            await groww_client.place_order(
                symbol=position["symbol"],
                qty=position["qty"],
                price=ltp,
                action=exit_action,
                product="MIS",
                order_type="MARKET",
            )
            if position.get("gtt_order_id"):
                await groww_client.cancel_gtt(position["gtt_order_id"])

            db = SessionLocal()
            try:
                await self._close_position(position["id"], ltp, "target_hit", db)
            finally:
                db.close()
        except Exception as exc:
            await broadcast_agent_log(
                "execution",
                "error",
                f"Failed to exit at target: {str(exc)}",
            )
        return True

    def _is_squareoff_time(self) -> bool:
        now_ist = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Kolkata"))
        return now_ist.hour > SQUAREOFF_HOUR_IST or (
            now_ist.hour == SQUAREOFF_HOUR_IST and now_ist.minute >= SQUAREOFF_MINUTE_IST
        )

    async def _monitor_positions(self):
        while True:
            if not self._active_positions:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            if self._is_squareoff_time():
                await broadcast_agent_log(
                    "execution",
                    "warning",
                    "15:10 IST — Force closing all MIS positions",
                )
                closed_count = 0
                total_closed_pnl = 0.0
                for position_id in list(self._active_positions.keys()):
                    pos = self._active_positions[position_id]
                    try:
                        ltp_data = await groww_client.get_ltp([pos["symbol"]])
                        ltp = ltp_data.get(pos["symbol"], pos["entry_price"])
                        pos_action = pos.get("action", "BUY")
                        exit_action = "SELL" if pos_action == "BUY" else "BUY"
                        await broadcast_agent_log(
                            "execution",
                            "warning",
                            f"15:10 IST square-off: "
                            f"{exit_action} {pos['qty']} "
                            f"{pos['symbol']} @ ₹{ltp:.2f} "
                            f"({'long' if pos_action == 'BUY' else 'short'} position)",
                        )
                        await groww_client.place_order(
                            symbol=pos["symbol"],
                            qty=pos["qty"],
                            price=ltp,
                            action=exit_action,
                            product="MIS",
                            order_type="MARKET",
                        )
                        if pos.get("gtt_order_id"):
                            await groww_client.cancel_gtt(pos["gtt_order_id"])

                        db = SessionLocal()
                        try:
                            closed = await self._close_position(
                                position_id,
                                ltp,
                                "squaredoff",
                                db,
                            )
                            if closed:
                                closed_count += 1
                        finally:
                            db.close()
                    except Exception as exc:
                        await broadcast_agent_log(
                            "execution",
                            "error",
                            f"Squareoff failed for {pos['symbol']}: {str(exc)}",
                        )
                await telegram.notify_squareoff_done(
                    position_count=closed_count,
                    total_pnl=total_closed_pnl,
                )
                break

            symbols = list({p["symbol"] for p in self._active_positions.values()})
            try:
                ltp_data = await groww_client.get_ltp(symbols)
            except Exception as exc:
                await broadcast_agent_log(
                    "execution",
                    "warning",
                    f"LTP fetch failed: {str(exc)}",
                )
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            for position_id, position in list(self._active_positions.items()):
                symbol = position["symbol"]
                ltp = ltp_data.get(symbol)
                if ltp is None:
                    continue

                self._active_positions[position_id]["current_ltp"] = ltp
                pnl_change = ltp - position["entry_price"]
                await broadcast_ltp_update(
                    symbol=symbol,
                    ltp=ltp,
                    change=round(pnl_change, 2),
                    change_pct=round((pnl_change / position["entry_price"]) * 100, 2),
                )
                await self._check_target_hit(position, ltp)

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def execute(
        self,
        signal: Signal,
        db: Session | None = None,
    ) -> Position | None:
        _ = db
        work_db = SessionLocal()
        try:
            signal_row = work_db.query(Signal).filter(Signal.id == signal.id).first() or signal
            self.is_running = True
            self._last_order = None
            await broadcast_agent_status("execution", "running", None)
            await broadcast_agent_log(
                "execution",
                "info",
                f"Execution started for {signal_row.action} {signal_row.symbol}",
            )

            try:
                margin = await asyncio.wait_for(
                    groww_client.get_margin(),
                    timeout=10.0,
                )
                available = margin.get("available_margin", 0)
                required = signal_row.entry_price * signal_row.qty
                if available < required:
                    await broadcast_agent_log(
                        "execution",
                        "error",
                        f"Insufficient margin: need ₹{required:.2f}, have ₹{available:.2f}",
                    )
                    return None
                await broadcast_agent_log(
                    "execution",
                    "info",
                    f"Margin OK: ₹{available:.2f} available, ₹{required:.2f} required",
                )
            except asyncio.TimeoutError:
                config = work_db.query(Config).filter(Config.id == 1).first()
                fallback_capital = config.capital_limit if config else 5000.0
                margin = {"available_margin": fallback_capital}
                available = margin["available_margin"]
                required = signal_row.entry_price * signal_row.qty
                await broadcast_agent_log(
                    "execution",
                    "warning",
                    "Margin check timed out, using capital_limit as available margin",
                )
                if available < required:
                    await broadcast_agent_log(
                        "execution",
                        "error",
                        f"Insufficient margin: need ₹{required:.2f}, have ₹{available:.2f}",
                    )
                    return None
            except Exception as exc:
                await broadcast_agent_log(
                    "execution",
                    "warning",
                    f"Margin check failed, proceeding: {str(exc)}",
                )

            if not is_entry_allowed():
                await broadcast_agent_log(
                    "execution",
                    "warning",
                    f"Order blocked — past 15:00 IST entry cutoff. "
                    f"Cannot open new MIS position this close to market close.",
                )
                from datetime import datetime
                from zoneinfo import ZoneInfo
                _ist_now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M:%S")
                await telegram._send(
                    f"⛔ <b>Order Blocked</b>\n\n"
                    f"Signal: {signal_row.action} {signal_row.symbol}\n"
                    f"Reason: Past 15:00 IST entry cutoff\n"
                    f"No new MIS positions allowed after 15:00 IST\n"
                    f"⏰ {_ist_now} IST"
                )
                self.is_running = False
                await broadcast_agent_status("execution", "stopped", None)
                return None

            entry_order = await self._place_entry_order(signal_row, work_db)
            if entry_order is None:
                return None
            self._last_order = entry_order

            gtt_order = await self._place_gtt_stoploss(
                signal_row,
                entry_order["groww_order_id"],
            )

            position = await self._create_position(
                signal_row,
                entry_order,
                gtt_order,
                work_db,
            )

            if self._monitoring_task is None or self._monitoring_task.done():
                self._monitoring_task = asyncio.create_task(self._monitor_positions())
                await broadcast_agent_log(
                    "execution",
                    "info",
                    "Position monitor started (polls every 30s)",
                )

            await broadcast_agent_status("execution", "stopped", None)
            await broadcast_agent_log(
                "execution",
                "success",
                f"Execution complete: {signal_row.symbol} position open | "
                f"Target: ₹{signal_row.target} | SL: ₹{signal_row.stoploss}",
            )
            return position
        finally:
            work_db.close()
            self.is_running = False

    async def manual_squareoff(self, position_id: str) -> bool:
        pos = self._active_positions.get(position_id)
        if not pos:
            return False

        try:
            ltp_data = await groww_client.get_ltp([pos["symbol"]])
            ltp = ltp_data.get(pos["symbol"], pos["entry_price"])
            pos_action = pos.get("action", "BUY")
            exit_action = "SELL" if pos_action == "BUY" else "BUY"

            await groww_client.place_order(
                symbol=pos["symbol"],
                qty=pos["qty"],
                price=ltp,
                action=exit_action,
                product="MIS",
                order_type="MARKET",
            )
            if pos.get("gtt_order_id"):
                await groww_client.cancel_gtt(pos["gtt_order_id"])

            db = SessionLocal()
            try:
                await self._close_position(position_id, ltp, "manual", db)
            finally:
                db.close()
            return True
        except Exception as exc:
            await broadcast_agent_log(
                "execution",
                "error",
                f"Manual squareoff failed: {str(exc)}",
            )
            return False

    def get_status(self) -> dict:
        return {
            "is_running": self.is_running,
            "active_positions": len(self._active_positions),
            "monitoring": self._monitoring_task is not None
            and not self._monitoring_task.done(),
            "last_order": self._last_order,
        }

    def get_active_positions(self) -> list:
        return list(self._active_positions.values())


execution_agent = ExecutionAgent()
