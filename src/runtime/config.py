"""
RuntimeConfig contains only the configuration fields needed by the runtime layer.

This separates runtime from src.app.settings, allowing cleaner architecture
and easier testing.
"""

from dataclasses import dataclass, field


@dataclass
class RuntimeConfig:
    """Configuration for the runtime layer."""

    # Market data
    market_data_window_candles: int = 300

    # LLM settings
    llm_enabled: bool = True
    llm_timeout_seconds: float = 60.0

    # Per-task timeouts (task_name -> timeout in seconds)
    task_timeouts: dict[str, float] = field(default_factory=dict)

    # Verifier settings
    verifier_enabled: bool = False
    verifier_mode: str = "soft"
    verifier_max_repairs: int = 1

    # Loop settings
    mvp_timeframe: str = "1m"
    mvp_symbols: list[str] = field(default_factory=lambda: ["EURUSD", "GBPUSD", "USDJPY"])

    def get_timeout_for_task(self, task: str) -> float:
        """Get timeout for a specific task, falling back to global timeout."""
        task_prefix_map = {
            "tech_analysis": "tech",
            "news_analysis": "news",
            "synthesis": "synthesis",
            "verification": "verifier",
        }
        task_prefix = task_prefix_map.get(task)
        if task_prefix:
            timeout_key = f"{task_prefix}_timeout_seconds"
            if timeout_key in self.task_timeouts:
                return self.task_timeouts[timeout_key]
        return self.llm_timeout_seconds
