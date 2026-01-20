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

        return "\n".join(lines)
