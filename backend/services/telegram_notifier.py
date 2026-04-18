import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx


logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def _ist_now() -> str:
    return datetime.now(IST).strftime("%H:%M:%S")


class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = TELEGRAM_API_BASE

        if self.enabled:
            logger.info("[Telegram] Notifier enabled. Chat ID: %s", self.chat_id)
        else:
            logger.warning(
                "[Telegram] Notifier disabled. Set TELEGRAM_BOT_TOKEN and "
                "TELEGRAM_CHAT_ID in .env to enable."
            )

    async def _send(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.enabled:
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True,
                    },
                )
            if response.status_code == 200:
                return True
            logger.warning(
                "[Telegram] Send failed: %s %s",
                response.status_code,
                response.text,
            )
            return False
        except Exception as exc:
            logger.error("[Telegram] Error: %s", exc)
            return False

    async def notify_scan_started(self, symbol_count: int):
        await self._send(
            f"🔍 <b>Scan Started</b>\n"
            f"Scanning {symbol_count} symbols\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_signal_found(
        self,
        symbol: str,
        action: str,
        entry: float,
        target: float,
        stoploss: float,
        qty: int,
        rsi: float,
        confidence: int,
        mode: str,
    ):
        mode_badge = "🧪 PAPER" if mode == "paper" else "💰 LIVE"
        if action == "SELL":
            reward = entry - target
            risk = stoploss - entry
            rr = round(reward / risk, 2) if risk > 0 else 0
            await self._send(
                f"📡 <b>Signal Found</b> {mode_badge} 📉 SHORT\n\n"
                f"<b>{action} {symbol}</b>\n"
                f"Entry:  ₹{entry}\n"
                f"Drop:   ₹{target} (-{((entry-target)/entry*100):.2f}%)\n"
                f"SL:     ₹{stoploss} (+{((stoploss-entry)/entry*100):.2f}%)\n"
                f"Qty:    {qty} shares\n"
                f"Value:  ₹{entry*qty:.2f}\n\n"
                f"RSI: {rsi} | R:R: {rr} | Conf: {confidence}%\n"
                f"⏰ {_ist_now()} IST"
            )
        else:
            rr = round((target - entry) / (entry - stoploss), 2) if entry != stoploss else 0
            await self._send(
                f"📡 <b>Signal Found</b> {mode_badge}\n\n"
                f"<b>{action} {symbol}</b>\n"
                f"Entry:  ₹{entry}\n"
                f"Target: ₹{target} (+{((target-entry)/entry*100):.2f}%)\n"
                f"SL:     ₹{stoploss} (-{((entry-stoploss)/entry*100):.2f}%)\n"
                f"Qty:    {qty} shares\n"
                f"Value:  ₹{entry*qty:.2f}\n\n"
                f"RSI: {rsi} | R:R: {rr} | Conf: {confidence}%\n"
                f"⏰ {_ist_now()} IST"
            )

    async def notify_signal_rejected(
        self,
        symbol: str,
        action: str,
        entry: float,
        reason: str,
    ):
        await self._send(
            f"❌ <b>Signal Rejected</b>\n\n"
            f"{action} {symbol} @ ₹{entry}\n"
            f"Reason: {reason}\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_no_signal(self, reason: str):
        await self._send(
            f"📊 <b>Scan Complete</b>\n"
            f"No signal: {reason}\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_order_placed(
        self,
        symbol: str,
        action: str,
        qty: int,
        price: float,
        order_id: str,
        mode: str,
    ):
        mode_badge = "🧪 PAPER" if mode == "paper" else "💰 LIVE"
        short_badge = " 📉 SHORT" if action == "SELL" else ""
        await self._send(
            f"✅ <b>Order Placed</b> {mode_badge}{short_badge}\n\n"
            f"<b>{action} {qty} {symbol}</b>\n"
            f"Price:    ₹{price}\n"
            f"Value:    ₹{price*qty:.2f}\n"
            f"Order ID: <code>{order_id}</code>\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_gtt_placed(
        self,
        symbol: str,
        qty: int,
        stoploss: float,
        gtt_id: str,
    ):
        await self._send(
            f"🛡️ <b>GTT Stoploss Active</b>\n\n"
            f"{qty} {symbol}\n"
            f"Trigger: ₹{stoploss}\n"
            f"GTT ID: <code>{gtt_id}</code>\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_target_hit(
        self,
        symbol: str,
        qty: int,
        entry: float,
        exit_price: float,
        pnl: float,
        pnl_pct: float,
        mode: str,
        action: str = "BUY",
    ):
        mode_badge = "🧪 PAPER" if mode == "paper" else "💰 LIVE"
        title = "🎯 Short Target Hit!" if action == "SELL" else "🎯 Target Hit!"
        await self._send(
            f"{title} {mode_badge}\n\n"
            f"<b>{symbol}</b> — {qty} shares\n"
            f"Entry:  ₹{entry}\n"
            f"Exit:   ₹{exit_price}\n"
            f"P&L:    <b>+₹{pnl:.2f} (+{pnl_pct:.2f}%)</b>\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_stoploss_hit(
        self,
        symbol: str,
        qty: int,
        entry: float,
        exit_price: float,
        pnl: float,
        pnl_pct: float,
        mode: str,
    ):
        mode_badge = "🧪 PAPER" if mode == "paper" else "💰 LIVE"
        await self._send(
            f"🛑 <b>Stoploss Hit</b> {mode_badge}\n\n"
            f"<b>{symbol}</b> — {qty} shares\n"
            f"Entry:  ₹{entry}\n"
            f"Exit:   ₹{exit_price}\n"
            f"P&L:    <b>₹{pnl:.2f} ({pnl_pct:.2f}%)</b>\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_squareoff_warning(self):
        await self._send(
            f"⚠️ <b>Square-off in 5 Minutes</b>\n\n"
            f"All open MIS positions will be\n"
            f"closed at 15:10 IST.\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_squareoff_done(self, position_count: int, total_pnl: float):
        emoji = "🟢" if total_pnl >= 0 else "🔴"
        await self._send(
            f"🔒 <b>Square-off Complete</b>\n\n"
            f"{position_count} position(s) closed\n"
            f"Total P&L: {emoji} <b>₹{total_pnl:.2f}</b>\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_token_refresh(self):
        await self._send(
            f"🔑 <b>Daily Token Reset</b>\n\n"
            f"Groww token has been invalidated.\n"
            f"Please approve today's session:\n"
            f"groww.in/user/profile/trading-apis\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_scanner_error(self, error: str):
        await self._send(
            f"🚨 <b>Scanner Error</b>\n\n"
            f"{error}\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_market_open(self):
        await self._send(
            f"📈 <b>Market Opens in 1 Minute</b>\n\n"
            f"First scan at 09:15 IST\n"
            f"⏰ {_ist_now()} IST"
        )

    async def notify_daily_summary(
        self,
        trades_today: int,
        pnl_today: float,
        signals_today: int,
        win_rate: float,
    ):
        emoji = "🟢" if pnl_today >= 0 else "🔴"
        await self._send(
            f"📊 <b>Daily Summary</b>\n\n"
            f"Trades:   {trades_today}\n"
            f"Signals:  {signals_today}\n"
            f"Win Rate: {win_rate:.1f}%\n"
            f"P&L:      {emoji} <b>₹{pnl_today:.2f}</b>\n"
            f"⏰ {_ist_now()} IST"
        )

    async def test_connection(self) -> bool:
        return await self._send(
            f"✅ <b>Groww Bot Connected</b>\n\n"
            f"Telegram notifications active.\n"
            f"Mode: {os.getenv('MODE', 'paper').upper()}\n"
            f"⏰ {_ist_now()} IST"
        )


telegram = TelegramNotifier()
