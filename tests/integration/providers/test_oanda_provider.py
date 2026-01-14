from datetime import datetime
from typing import Any
from unittest.mock import Mock

import httpx

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.data_providers.forex.oanda_provider import OandaProvider


def test_fetch_candles_parses_oanda_response() -> None:
    mock_response_data: dict[str, Any] = {
        "candles": [
            {
                "time": "2024-01-01T12:00:00.000000000Z",
                "mid": {
                    "o": "1.1000",
                    "h": "1.1010",
                    "l": "1.0990",
                    "c": "1.1005",
                },
                "volume": 1000,
                "complete": True,
            },
            {
                "time": "2024-01-01T13:00:00.000000000Z",
                "mid": {
                    "o": "1.1005",
                    "h": "1.1020",
                    "l": "1.1000",
                    "c": "1.1015",
                },
                "volume": 1500,
                "complete": True,
            },
        ]
    }

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = OandaProvider(api_key="test-key", base_url="https://api.test.com")
    provider.client = mock_client

    candles = provider.fetch_candles(
        symbol="EUR_USD",
        timeframe=Timeframe.H1,
        count=2,
    )

    assert len(candles) == 2
    assert isinstance(candles[0], Candle)
    assert candles[0].timestamp == datetime.fromisoformat("2024-01-01T12:00:00+00:00")
    assert candles[0].open == 1.1000
    assert candles[0].high == 1.1010
    assert candles[0].low == 1.0990
    assert candles[0].close == 1.1005
    assert candles[0].volume == 1000.0

    assert candles[1].timestamp == datetime.fromisoformat("2024-01-01T13:00:00+00:00")
    assert candles[1].close == 1.1015


def test_fetch_candles_skips_incomplete_candles() -> None:
    mock_response_data: dict[str, Any] = {
        "candles": [
            {
                "time": "2024-01-01T12:00:00.000000000Z",
                "mid": {
                    "o": "1.1000",
                    "h": "1.1010",
                    "l": "1.0990",
                    "c": "1.1005",
                },
                "volume": 1000,
                "complete": True,
            },
            {
                "time": "2024-01-01T13:00:00.000000000Z",
                "mid": {
                    "o": "1.1005",
                    "h": "1.1020",
                    "l": "1.1000",
                    "c": "1.1015",
                },
                "volume": 1500,
                "complete": False,
            },
        ]
    }

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = OandaProvider(api_key="test-key", base_url="https://api.test.com")
    provider.client = mock_client

    candles = provider.fetch_candles(
        symbol="EUR_USD",
        timeframe=Timeframe.H1,
        count=2,
    )

    assert len(candles) == 1
    assert candles[0].close == 1.1005


def test_fetch_candles_with_date_range() -> None:
    mock_response_data: dict[str, list[dict[str, Any]]] = {"candles": []}

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = OandaProvider(api_key="test-key", base_url="https://api.test.com")
    provider.client = mock_client

    from_time = datetime(2024, 1, 1, 12, 0, 0)
    to_time = datetime(2024, 1, 1, 13, 0, 0)

    provider.fetch_candles(
        symbol="EUR_USD",
        timeframe=Timeframe.H1,
        count=100,
        from_time=from_time,
        to_time=to_time,
    )

    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "from" in call_args.kwargs["params"]
    assert "to" in call_args.kwargs["params"]


def test_convert_timeframe_to_oanda() -> None:
    provider = OandaProvider(api_key="test-key", base_url="https://api.test.com")

    assert provider._convert_timeframe_to_oanda(Timeframe.M1) == "M1"
    assert provider._convert_timeframe_to_oanda(Timeframe.M5) == "M5"
    assert provider._convert_timeframe_to_oanda(Timeframe.M15) == "M15"
    assert provider._convert_timeframe_to_oanda(Timeframe.H1) == "H1"
    assert provider._convert_timeframe_to_oanda(Timeframe.D1) == "D"
