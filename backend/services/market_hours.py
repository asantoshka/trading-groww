import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
LAST_ENTRY_TIME = time(15, 0)

NSE_HOLIDAY_URL = "https://www.nseindia.com/api/holiday-master?type=trading"

_holiday_cache: set[date] = set()
_cache_loaded: bool = False


async def fetch_nse_holidays() -> None:
    global _holiday_cache, _cache_loaded

    try:
        async with httpx.AsyncClient(
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Referer": "https://www.nseindia.com",
            },
        ) as client:
            response = await client.get(NSE_HOLIDAY_URL)

        if response.status_code == 200:
            data = response.json()
            holidays: set[date] = set()
            for month_key, month_holidays in data.items():
                if isinstance(month_holidays, list):
                    for holiday in month_holidays:
                        date_str = holiday.get("tradingDate", "")
                        if date_str:
                            try:
                                parsed = datetime.strptime(date_str, "%d-%b-%Y").date()
                                holidays.add(parsed)
                            except ValueError:
                                continue
            _holiday_cache = holidays
            _cache_loaded = True
            logger.info(
                "[MarketHours] Loaded %d NSE holidays from NSE API",
                len(holidays),
            )
        else:
            logger.warning(
                "[MarketHours] NSE holiday API returned %s. "
                "Using empty holiday list.",
                response.status_code,
            )
            _cache_loaded = True

    except Exception as e:
        logger.warning(
            "[MarketHours] Failed to fetch NSE holidays: %s. "
            "Weekend detection still works. "
            "Holidays will not be detected.",
            e,
        )
        _cache_loaded = True


def is_nse_holiday(d: date) -> bool:
    return d in _holiday_cache


def is_market_open() -> bool:
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    if is_nse_holiday(now.date()):
        return False
    current_time = now.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def is_trading_day() -> bool:
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    if is_nse_holiday(now.date()):
        return False
    return True


def get_market_status() -> dict:
    now = datetime.now(IST)
    current_time = now.time()
    today = now.date()

    is_weekend = now.weekday() >= 5
    is_holiday = is_nse_holiday(today)
    is_open = is_market_open()

    if is_weekend:
        day = "Saturday" if now.weekday() == 5 else "Sunday"
        status = "weekend"
        message = f"Market closed — {day}"
    elif is_holiday:
        status = "holiday"
        message = "Market closed — NSE Holiday"
    elif current_time < MARKET_OPEN:
        status = "pre_market"
        message = "Pre-market — Opens at 09:15 IST"
    elif current_time > MARKET_CLOSE:
        status = "closed"
        message = "Market closed for today"
    else:
        status = "open"
        message = "Market is open"

    return {
        "status": status,
        "is_open": is_open,
        "is_trading_day": is_trading_day(),
        "is_holiday": is_holiday,
        "entry_allowed": is_entry_allowed(),
        "minutes_to_close": get_time_to_close(),
        "minutes_to_last_entry": get_time_to_last_entry(),
        "holidays_loaded": _cache_loaded,
        "holiday_count": len(_holiday_cache),
        "message": message,
        "current_time_ist": now.strftime("%H:%M:%S IST"),
        "date": today.isoformat(),
    }


def is_entry_allowed() -> bool:
    """Returns True only if market is open and current time is before 15:00 IST."""
    if not is_market_open():
        return False
    now = datetime.now(IST)
    if now.time() >= LAST_ENTRY_TIME:
        return False
    return True


def get_time_to_close() -> int:
    """Returns minutes remaining until market close (15:30 IST). 0 if closed."""
    now = datetime.now(IST)
    if not is_market_open():
        return 0
    close = datetime.combine(now.date(), MARKET_CLOSE, tzinfo=IST)
    delta = close - now
    return max(0, int(delta.total_seconds() / 60))


def get_time_to_last_entry() -> int:
    """Returns minutes remaining until last entry cutoff (15:00 IST). 0 if past cutoff."""
    now = datetime.now(IST)
    if not is_market_open():
        return 0
    cutoff = datetime.combine(now.date(), LAST_ENTRY_TIME, tzinfo=IST)
    delta = cutoff - now
    return max(0, int(delta.total_seconds() / 60))


def next_market_open() -> str:
    now = datetime.now(IST)
    for days_ahead in range(1, 15):
        next_day = now.date() + timedelta(days=days_ahead)
        if next_day.weekday() < 5 and not is_nse_holiday(next_day):
            return f"{next_day.strftime('%A %d %b')} at 09:15 IST"
    return "Next trading day at 09:15 IST"
