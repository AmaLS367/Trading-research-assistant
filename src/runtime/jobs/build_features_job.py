from datetime import datetime

from src.core.models.candle import Candle
from src.core.models.signal import Signal
from src.core.models.timeframe import Timeframe
from src.features.contracts.feature_contract import FeatureContract, ValidationStatus
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
            validation_result = FeatureContract.validate(candles, min_count=200)
            if validation_result.status == ValidationStatus.INVALID:
                reasons_text = "; ".join(validation_result.reasons)
                return JobResult[tuple[FeatureSnapshot, Signal]](
                    ok=False,
                    value=None,
                    error=f"Invalid candle data: {reasons_text}",
                )

            indicators = calculate_features(candles)

            snapshot = FeatureSnapshot(
                timestamp=datetime.now(),
                candles=candles,
                indicators=indicators,
                validation_status=validation_result.status,
                validation_reasons=validation_result.reasons,
                validated_candle_count=validation_result.candle_count,
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
