from datetime import datetime

import httpx

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider
from src.utils.retry import retry_network_call


class TwelveDataProvider(MarketDataProvider):
    def __init__(self, api_key: str, base_url: str, timeout: float = 30.0) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _convert_symbol_to_twelve_data(self, symbol: str) -> str:
        symbol_upper = symbol.upper().strip()
        if "/" in symbol_upper:
            return symbol_upper
        if len(symbol_upper) == 6:
            return f"{symbol_upper[:3]}/{symbol_upper[3:]}"
        return symbol_upper.replace("_", "/")

    def _convert_timeframe_to_twelve_data(self, timeframe: Timeframe) -> str:
        mapping = {
            Timeframe.M1: "1min",
            Timeframe.M5: "5min",
            Timeframe.M15: "15min",
            Timeframe.H1: "1h",
            Timeframe.D1: "1day",
        }
        return mapping[timeframe]

    @retry_network_call
    def fetch_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> list[Candle]:
        twelve_data_symbol = self._convert_symbol_to_twelve_data(symbol)
        twelve_data_interval = self._convert_timeframe_to_twelve_data(timeframe)
        url = f"{self.base_url}/time_series"

        params: dict[str, str | int] = {
            "symbol": twelve_data_symbol,
            "interval": twelve_data_interval,
            "apikey": self.api_key,
            "outputsize": count,
        }

        if from_time is not None:
            params["start_date"] = from_time.strftime("%Y-%m-%d %H:%M:%S")
        if to_time is not None:
            params["end_date"] = to_time.strftime("%Y-%m-%d %H:%M:%S")

        response = self.client.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            error_message = data.get("message", "Unknown error from TwelveData API")
            raise ValueError(f"TwelveData API error: {error_message}")

        if "status" in data and data["status"] != "ok":
            error_message = data.get("message", "Unknown error from TwelveData API")
            raise ValueError(f"TwelveData API error: {error_message}")

        values = data.get("values", [])
        if not values:
            return []

        candles: list[Candle] = []
        for value in values:
            try:
                timestamp_str = value.get("datetime", "")
                if not timestamp_str:
                    continue

                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                open_price = float(value.get("open", 0))
                high_price = float(value.get("high", 0))
                low_price = float(value.get("low", 0))
                close_price = float(value.get("close", 0))
                volume = float(value.get("volume", 0))

                candles.append(
                    Candle(
                        timestamp=timestamp,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume,
                    )
                )
            except (ValueError, KeyError, TypeError):
                continue

        candles.sort(key=lambda c: c.timestamp)

        return candles

    def __del__(self) -> None:
        if hasattr(self, "client"):
            self.client.close()
