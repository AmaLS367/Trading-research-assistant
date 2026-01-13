from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider
from src.runtime.jobs.job_result import JobResult


class FetchMarketDataJob:
    def __init__(self, market_data_provider: MarketDataProvider) -> None:
        self.market_data_provider = market_data_provider

    def run(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int = 300,
    ) -> JobResult[list[Candle]]:
        try:
            candles = self.market_data_provider.fetch_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=count,
            )

            if len(candles) < 200:
                return JobResult(
                    ok=False,
                    value=None,
                    error=f"Insufficient candles: got {len(candles)}, need at least 200",
                )

            return JobResult(ok=True, value=candles, error="")

        except Exception as e:
            return JobResult(
                ok=False,
                value=None,
                error=f"Failed to fetch market data: {str(e)}",
            )
