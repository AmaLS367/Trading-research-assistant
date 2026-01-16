from datetime import datetime

from src.core.models.candle import Candle
from src.core.models.signal import Signal
from src.core.models.timeframe import Timeframe
from src.features.indicators.indicator_engine import calculate_features
from src.features.regime.regime_detector import RegimeDetector
from src.features.snapshots.feature_snapshot import FeatureSnapshot
from src.features.volatility.volatility_estimator import VolatilityEstimator
from src.runtime.jobs.job_result import JobResult


class BuildFeaturesJob:
    def run(
        self,
        symbol: str,
        timeframe: Timeframe,
        candles: list[Candle],
    ) -> JobResult[tuple[FeatureSnapshot, Signal]]:
        try:
            if len(candles) < 200:
                return JobResult[tuple[FeatureSnapshot, Signal]](
                    ok=False,
                    value=None,
                    error=f"Insufficient candles: got {len(candles)}, need at least 200",
                )

            indicators = calculate_features(candles)

            snapshot = FeatureSnapshot(
                timestamp=datetime.now(),
                candles=candles,
                indicators=indicators,
            )

            regime = RegimeDetector.detect(candles)
            volatility = VolatilityEstimator.estimate(candles)

            signal = Signal(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.now(),
                indicators=indicators,
                regime=regime,
                volatility=volatility,
            )

            return JobResult[tuple[FeatureSnapshot, Signal]](
                ok=True, value=(snapshot, signal), error=""
            )

        except Exception as e:
            return JobResult[tuple[FeatureSnapshot, Signal]](
                ok=False,
                value=None,
                error=f"Failed to build features: {str(e)}",
            )
