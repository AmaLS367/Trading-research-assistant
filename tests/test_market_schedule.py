from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils.market_schedule import is_forex_market_open

NY_TZ = ZoneInfo("America/New_York")


def test_friday_1659_open() -> None:
    dt = datetime(2024, 1, 5, 16, 59, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is True


def test_friday_1700_closed() -> None:
    dt = datetime(2024, 1, 5, 17, 0, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is False


def test_saturday_closed() -> None:
    dt = datetime(2024, 1, 6, 12, 0, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is False


def test_sunday_1659_closed() -> None:
    dt = datetime(2024, 1, 7, 16, 59, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is False


def test_sunday_1700_open() -> None:
    dt = datetime(2024, 1, 7, 17, 0, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is True


def test_monday_open() -> None:
    dt = datetime(2024, 1, 8, 12, 0, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is True


def test_tuesday_open() -> None:
    dt = datetime(2024, 1, 9, 12, 0, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is True


def test_wednesday_open() -> None:
    dt = datetime(2024, 1, 10, 12, 0, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is True


def test_thursday_open() -> None:
    dt = datetime(2024, 1, 11, 12, 0, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is True


def test_friday_morning_open() -> None:
    dt = datetime(2024, 1, 5, 9, 0, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is True


def test_sunday_evening_open() -> None:
    dt = datetime(2024, 1, 7, 23, 59, 0, tzinfo=NY_TZ)
    assert is_forex_market_open(dt) is True
