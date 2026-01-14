from datetime import datetime

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider


class OandaProvider(MarketDataProvider):
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    def _convert_timeframe_to_oanda(self, timeframe: Timeframe) -> str:
        mapping = {
            Timeframe.M1: "M1",
            Timeframe.M5: "M5",
            Timeframe.M15: "M15",
            Timeframe.H1: "H1",
            Timeframe.D1: "D",
        }
        return mapping[timeframe]

    def _format_datetime_for_oanda(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")

    def _convert_symbol_to_oanda(self, symbol: str) -> str:
        symbol_upper = symbol.upper().strip()
        if "_" in symbol_upper:
            return symbol_upper
        if len(symbol_upper) == 6:
            return f"{symbol_upper[:3]}_{symbol_upper[3:]}"
        return symbol_upper

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    def fetch_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> list[Candle]:
        oanda_symbol = self._convert_symbol_to_oanda(symbol)
        oanda_timeframe = self._convert_timeframe_to_oanda(timeframe)
        url = f"{self.base_url}/v3/instruments/{oanda_symbol}/candles"

        params: dict[str, str | int] = {
            "granularity": oanda_timeframe,
            "count": count,
        }

        if from_time is not None:
            params["from"] = self._format_datetime_for_oanda(from_time)
        if to_time is not None:
            params["to"] = self._format_datetime_for_oanda(to_time)

        response = self.client.get(url, params=params)

        if response.status_code == 400:
            error_data = (
                response.json()
                if response.headers.get("content-type", "").startswith("application/json")
                else {}
            )
            error_message = error_data.get("errorMessage", "Bad Request")
            raise ValueError(
                f"OANDA API error: {error_message}. Symbol: {symbol} -> {oanda_symbol}"
            )

        response.raise_for_status()

        data = response.json()
        candles_data = data.get("candles", [])

        candles: list[Candle] = []
        for candle_data in candles_data:
            if not candle_data.get("complete", False):
                continue

            mid = candle_data.get("mid")
            if mid is None:
                continue

            time_str = candle_data.get("time")
            if time_str is None:
                continue

            timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

            candles.append(
                Candle(
                    timestamp=timestamp,
                    open=float(mid["o"]),
                    high=float(mid["h"]),
                    low=float(mid["l"]),
                    close=float(mid["c"]),
                    volume=float(candle_data.get("volume", 0)),
                )
            )

        return candles

    def __del__(self) -> None:
        if hasattr(self, "client"):
            self.client.close()
