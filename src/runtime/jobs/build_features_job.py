from datetime import datetime

from src.core.models.candle import Candle
from src.core.models.signal import Signal
from src.core.models.timeframe import Timeframe
from src.features.contracts.feature_contract import FeatureContract, ValidationStatus
from src.features.derived.basic_derived import calculate_basic_derived
from src.features.derived.ma_distance import calculate_ma_distances
from src.features.derived.ma_slope import calculate_ma_slopes
from src.features.derived.momentum_derived import calculate_momentum_features
from src.features.derived.volatility_derived import calculate_bb_metrics
from src.features.indicators.indicator_engine import calculate_features
from src.features.regime.regime_detector import RegimeDetector
from src.features.snapshots.feature_snapshot import FeatureSnapshot
from src.features.trend.trend_detector import TrendDetector
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
            derived = calculate_basic_derived(candles)
            for key, value in derived.items():
                if key in indicators:
                    continue
                indicators[key] = value

            momentum = calculate_momentum_features(candles)
            for key, value in momentum.items():
                if key in indicators:
                    continue
                indicators[key] = value

            ma_slopes = calculate_ma_slopes(candles, slope_window=10)
            for key, value in ma_slopes.items():
                if key in indicators:
                    continue
                indicators[key] = value

            trend = TrendDetector.detect(candles, indicators)
            trend_direction = trend.get("trend_direction")
            trend_strength = trend.get("trend_strength")

            close_price = float(candles[-1].close)
            ma_distances = calculate_ma_distances(close_price, indicators)
            for key, value in ma_distances.items():
                if key in indicators:
                    continue
                indicators[key] = value

            bb_metrics = calculate_bb_metrics(close_price, indicators)
            for key, value in bb_metrics.items():
                if key in indicators:
                    continue
                indicators[key] = value

            snapshot = FeatureSnapshot(
                timestamp=datetime.now(),
                candles=candles,
                indicators=indicators,
                validation_status=validation_result.status,
                validation_reasons=validation_result.reasons,
                validated_candle_count=validation_result.candle_count,
                trend_direction=trend_direction if isinstance(trend_direction, str) else None,
                trend_strength=float(trend_strength)
                if isinstance(trend_strength, (int, float))
                else None,
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
