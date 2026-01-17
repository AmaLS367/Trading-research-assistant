from typing import Literal

import httpx

from src.app.settings import settings

_asset_type_cache: dict[str, Literal["forex", "crypto", "other", "unknown"]] = {}


def classify_symbol_asset_type(symbol: str) -> Literal["forex", "crypto", "other", "unknown"]:
    """
    Classify symbol asset type using Twelve Data API.

    Args:
        symbol: Trading symbol (e.g., EURUSD, BTCUSD)

    Returns:
        Asset type: "forex", "crypto", "other", or "unknown" if classification fails.
    """
    if symbol in _asset_type_cache:
        return _asset_type_cache[symbol]

    if not settings.twelve_data_api_key:
        return "unknown"

    symbol_upper = symbol.upper().strip()
    twelve_data_symbol = symbol_upper
    if "/" not in symbol_upper and len(symbol_upper) == 6:
        twelve_data_symbol = f"{symbol_upper[:3]}/{symbol_upper[3:]}"

    try:
        url = f"{settings.twelve_data_base_url}/symbol_search"
        params: dict[str, str] = {
            "symbol": twelve_data_symbol,
            "apikey": settings.twelve_data_api_key,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                _asset_type_cache[symbol] = "unknown"
                return "unknown"

            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                first_result = data["data"][0]
                symbol_type = first_result.get("type", "").lower()
                instrument_type = first_result.get("instrument_type", "").lower()
                exchange = first_result.get("exchange", "").upper()

                result: Literal["forex", "crypto", "other", "unknown"]
                is_forex_by_type = symbol_type == "forex"
                is_forex_by_instrument = instrument_type in ["physical currency", "forex"]
                is_forex_by_exchange = exchange == "PHYSICAL CURRENCY"
                is_forex = is_forex_by_type or is_forex_by_instrument or is_forex_by_exchange

                if is_forex:
                    result = "forex"
                elif symbol_type in ["crypto", "cryptocurrency"] or instrument_type in [
                    "crypto",
                    "cryptocurrency",
                ]:
                    result = "crypto"
                else:
                    result = "other"

                _asset_type_cache[symbol] = result
                return result

            _asset_type_cache[symbol] = "unknown"
            return "unknown"
    except Exception:
        _asset_type_cache[symbol] = "unknown"
        return "unknown"
