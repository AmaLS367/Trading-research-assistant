from datetime import datetime
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")


def is_forex_market_open(now: datetime | None = None) -> bool:
    """
    Check if Forex market is open based on NY timezone schedule.

    Schedule:
    - Friday: open until 17:00 NY, closed from 17:00
    - Saturday: closed
    - Sunday: closed until 17:00 NY, open from 17:00
    - Monday-Thursday: open

    Args:
        now: Optional datetime to check. If None, uses current time in NY timezone.

    Returns:
        True if market is open, False otherwise.
    """
    ny_now = datetime.now(NY_TZ) if now is None else now.astimezone(NY_TZ)

    weekday = ny_now.weekday()
    hour = ny_now.hour
    minute = ny_now.minute
    time_minutes = hour * 60 + minute

    if weekday == 4:
        return time_minutes < 17 * 60
    if weekday == 5:
        return False
    if weekday == 6:
        return time_minutes >= 17 * 60
    return True
