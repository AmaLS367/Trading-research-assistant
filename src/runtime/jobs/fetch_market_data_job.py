from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider
from src.runtime.jobs.job_result import JobResult
from src.storage.sqlite.repositories.candles_repository import CandlesRepository
from src.utils.logging import get_logger


class FetchMarketDataJob:
    def __init__(
        self,
        market_data_provider: MarketDataProvider,
        candles_repository: CandlesRepository | None = None,
    ) -> None:
        self.market_data_provider = market_data_provider
        self.candles_repository = candles_repository
        self.logger = get_logger(__name__)

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

            if self.candles_repository is not None:
                self.candles_repository.upsert_many(
                    symbol=symbol, timeframe=timeframe, candles=candles
                )

            return JobResult(ok=True, value=candles, error="")

        except Exception as e:
            self.logger.exception(f"Market data provider error for {symbol} {timeframe.value}: {e}")
            return JobResult(
                ok=False,
                value=None,
                error=f"Failed to fetch market data: {str(e)}",
            )
