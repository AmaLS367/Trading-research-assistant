import time
from datetime import UTC, datetime

from src.core.ports.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


def get_utc_now() -> datetime:
    return datetime.now(UTC)
