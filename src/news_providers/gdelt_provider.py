import httpx

from src.core.ports.news_provider import NewsProvider


class GDELTProvider(NewsProvider):
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _build_query_from_symbol(self, symbol: str) -> str:
        symbol_upper = symbol.upper().strip()
        if len(symbol_upper) == 6:
            return f"{symbol_upper[:3]} {symbol_upper[3:]}"
        return symbol_upper.replace("_", " ")

    def get_news_summary(self, symbol: str) -> str:
        try:
            query = self._build_query_from_symbol(symbol)
            url = f"{self.base_url}/api/v2/doc/doc"

            params: dict[str, str | int] = {
                "query": query,
                "mode": "artlist",
                "format": "json",
                "maxrecords": 5,
                "timespan": "24h",
                "sort": "datedesc",
            }

            response = self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            articles = data.get("articles", [])

            if not articles:
                return "No news found via GDELT."

            titles: list[str] = []
            for article in articles[:5]:
                title = article.get("title", "")
                if title:
                    titles.append(title.strip())

            if not titles:
                return "No news found via GDELT."

            result = "Latest news:\n"
            for title in titles:
                result += f"- {title}\n"

            return result.rstrip()

        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError):
            return "No news found via GDELT."
        except (KeyError, ValueError, TypeError):
            return "No news found via GDELT."
        except Exception:
            return "No news found via GDELT."

    def __del__(self) -> None:
        if hasattr(self, "client"):
            self.client.close()
