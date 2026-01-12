import warnings
from datetime import datetime

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider


class FallbackMarketDataProvider(MarketDataProvider):
    def __init__(
        self,
        primary: MarketDataProvider,
        secondary: MarketDataProvider | None = None,
    ) -> None:
        self.primary = primary
        self.secondary = secondary

    def fetch_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> list[Candle]:
        try:
            return self.primary.fetch_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=count,
                from_time=from_time,
                to_time=to_time,
            )
        except Exception as e:
            if self.secondary is None:
                raise

            primary_name = self.primary.__class__.__name__
            warning_msg = (
                f"{primary_name} failed: {e}. "
                f"Falling back to {self.secondary.__class__.__name__}."
            )
            warnings.warn(warning_msg, UserWarning, stacklevel=2)

            try:
                return self.secondary.fetch_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    count=count,
                    from_time=from_time,
                    to_time=to_time,
                )
            except Exception as secondary_error:
                secondary_name = self.secondary.__class__.__name__
                raise RuntimeError(
                    f"Both providers failed. Primary ({primary_name}): {e}. "
                    f"Secondary ({secondary_name}): {secondary_error}."
                ) from secondary_error
