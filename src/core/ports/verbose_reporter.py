from typing import Protocol


class VerboseReporter(Protocol):
    """
    Protocol for verbose output reporting during pipeline execution.

    Used to provide human-readable progress updates and results
    without coupling core domain logic to UI implementation.
    """

    def step_start(self, text: str) -> None:
        """
        Emit a step start message (e.g., "→ Fetching market data...").

        Args:
            text: Human-readable step description
        """
        ...

    def step_done(self, text: str) -> None:
        """
        Emit a step completion message (e.g., "✓ Loaded 299 candles").

        Args:
            text: Human-readable completion message
        """
        ...

    def panel(self, title: str, body: str) -> None:
        """
        Display a formatted panel with title and body content.

        Args:
            title: Panel title
            body: Panel body content (can be multi-line)
        """
        ...

    def llm_summary(
        self,
        tech: str,
        news: str,
        synthesis: str,
        verify: str,
    ) -> None:
        """
        Display a summary of LLM providers/models used for each task.

        Args:
            tech: Provider/model for technical analysis (e.g., "ollama/llama3.2")
            news: Provider/model for news analysis (e.g., "ollama/llama3.2" or "none")
            synthesis: Provider/model for synthesis (e.g., "ollama/llama3.2")
            verify: Provider/model for verification (e.g., "ollama/llama3.2" or "none")
        """
        ...
