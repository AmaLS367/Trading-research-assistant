import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.core.models.candle import Candle
from src.features.contracts.feature_contract import ValidationStatus


class FeatureSnapshot(BaseModel):
    timestamp: datetime
    candles: list[Candle]
    indicators: dict[str, float]
    validation_status: ValidationStatus = ValidationStatus.OK
    validation_reasons: list[str] = Field(default_factory=list)
    validated_candle_count: int | None = None
    trend_direction: str | None = None
    trend_strength: float | None = None
    ema9_sma50_crossover_type: str | None = None
    ema9_sma50_crossover_age_bars: int | None = None
    sma50_sma200_crossover_type: str | None = None
    sma50_sma200_crossover_age_bars: int | None = None
    candlestick_pattern: str | None = None
    candlestick_pattern_strength: float | None = None
    volume_trend: str | None = None

    @field_validator("indicators")
    @classmethod
    def check_nan(cls, v: dict[str, Any]) -> dict[str, float]:
        cleaned: dict[str, float] = {}
        for key, value in v.items():
            if isinstance(value, (int, float)):
                if math.isnan(value) or math.isinf(value):
                    raise ValueError(f"Indicator {key} contains NaN or Infinity")
                cleaned[key] = float(value)
            else:
                raise ValueError(f"Indicator {key} must be a number, got {type(value)}")
        return cleaned

    def to_markdown(self) -> str:
        lines: list[str] = []

        def format_float(value: float | None, decimals: int = 2, suffix: str = "") -> str:
            if value is None:
                return "N/A"
            if not isinstance(value, (int, float)):
                return "N/A"
            if math.isnan(value) or math.isinf(value):
                return "N/A"
            return f"{float(value):.{decimals}f}{suffix}"

        def get_indicator(key: str) -> float | None:
            value = self.indicators.get(key)
            if value is None:
                return None
            if not isinstance(value, (int, float)):
                return None
            if math.isnan(value) or math.isinf(value):
                return None
            return float(value)

        current_price = self.candles[-1].close if self.candles else 0.0
        lines.append(f"**Current Price:** {current_price:.5f}")

        rsi = self.indicators.get("rsi", 0.0)
        if rsi > 70:
            rsi_status = "Overbought"
        elif rsi < 30:
            rsi_status = "Oversold"
        else:
            rsi_status = "Neutral"
        lines.append(f"**RSI:** {rsi:.2f} ({rsi_status})")

        sma_50 = self.indicators.get("sma_50", 0.0)
        sma_200 = self.indicators.get("sma_200", 0.0)
        lines.append(f"**SMA 50:** {sma_50:.5f}")
        lines.append(f"**SMA 200:** {sma_200:.5f}")

        ema_9 = self.indicators.get("ema_9", 0.0)
        lines.append(f"**EMA 9:** {ema_9:.5f}")

        bb_upper = self.indicators.get("bb_upper", 0.0)
        bb_middle = self.indicators.get("bb_middle", 0.0)
        bb_lower = self.indicators.get("bb_lower", 0.0)
        lines.append(
            f"**Bollinger Bands:** Upper={bb_upper:.5f}, "
            f"Middle={bb_middle:.5f}, Lower={bb_lower:.5f}"
        )

        atr = self.indicators.get("atr", 0.0)
        lines.append(f"**ATR:** {atr:.5f}")

        lines.append("")
        lines.append("### Trend")
        lines.append(f"- **Direction:** {self.trend_direction or 'N/A'}")
        lines.append(f"- **Strength:** {format_float(self.trend_strength, decimals=1)}")

        lines.append("")
        lines.append("### Structure")
        lines.append("- **Market structure:** N/A")

        lines.append("")
        lines.append("### Momentum")
        lines.append(
            "- **RSI deltas:** "
            f"Δ1={format_float(get_indicator('rsi_delta_1'), decimals=2)}, "
            f"Δ5={format_float(get_indicator('rsi_delta_5'), decimals=2)}"
        )
        lines.append(
            "- **ROC:** "
            f"5={format_float(get_indicator('roc_5'), decimals=2, suffix='%')}, "
            f"20={format_float(get_indicator('roc_20'), decimals=2, suffix='%')}"
        )

        lines.append("")
        lines.append("### Crossovers")
        lines.append(
            "- **EMA9/SMA50:** "
            f"{self.ema9_sma50_crossover_type or 'N/A'} "
            f"(age: {self.ema9_sma50_crossover_age_bars if self.ema9_sma50_crossover_age_bars is not None else 'N/A'})"
        )
        lines.append(
            "- **SMA50/SMA200:** "
            f"{self.sma50_sma200_crossover_type or 'N/A'} "
            f"(age: {self.sma50_sma200_crossover_age_bars if self.sma50_sma200_crossover_age_bars is not None else 'N/A'})"
        )

        lines.append("")
        lines.append("### Volatility/BB")
        bb_position = get_indicator("bb_position")
        bb_bandwidth_pct = get_indicator("bb_bandwidth_pct")
        bb_squeeze_flag = get_indicator("bb_squeeze_flag")
        if bb_squeeze_flag is None:
            squeeze_text = "N/A"
        else:
            squeeze_text = "YES" if bb_squeeze_flag == 1.0 else "NO"
        lines.append(
            "- **BB:** "
            f"pos={format_float(bb_position, decimals=2)}, "
            f"bandwidth={format_float(bb_bandwidth_pct, decimals=2, suffix='%')}, "
            f"squeeze={squeeze_text}"
        )
        lines.append(
            "- **ATR:** "
            f"{format_float(get_indicator('atr'), decimals=5)}, "
            f"ATR%={format_float(get_indicator('atr_pct'), decimals=2, suffix='%')}"
        )

        lines.append("")
        lines.append("### Volume")
        vol_confirm = get_indicator("volume_confirmation_flag")
        if vol_confirm is None:
            confirm_text = "N/A"
        else:
            confirm_text = "YES" if vol_confirm == 1.0 else "NO"
        lines.append(f"- **Trend:** {self.volume_trend or 'N/A'}")
        lines.append(
            "- **Context:** "
            f"mean={format_float(get_indicator('volume_mean'), decimals=2)}, "
            f"z={format_float(get_indicator('volume_zscore'), decimals=2)}, "
            f"confirm={confirm_text}"
        )

        lines.append("")
        lines.append("### Patterns")
        lines.append(f"- **Pattern:** {self.candlestick_pattern or 'N/A'}")
        lines.append(f"- **Strength:** {format_float(self.candlestick_pattern_strength, decimals=1)}")

        return "\n".join(lines)
