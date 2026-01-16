from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.ports.verbose_reporter import VerboseReporter


class PipelineTrace:
    """
    Pipeline trace output for verbose mode.

    Wraps VerboseReporter to provide backward-compatible interface.
    When disabled, uses a no-op reporter.
    """

    def __init__(
        self,
        enabled: bool = False,
        reporter: "VerboseReporter | None" = None,
    ) -> None:
        self.enabled = enabled
        self.reporter = reporter

    def step_start(self, text: str) -> None:
        """Emit a step start message."""
        if self.enabled and self.reporter:
            self.reporter.step_start(text)

    def step_done(self, text: str) -> None:
        """Emit a step completion message."""
        if self.enabled and self.reporter:
            self.reporter.step_done(text)

    def panel(self, title: str, body: str) -> None:
        """Display a formatted panel."""
        if self.enabled and self.reporter:
            self.reporter.panel(title, body)

    def llm_summary(
        self,
        tech: str,
        news: str,
        synthesis: str,
        verify: str,
    ) -> None:
        """Display LLM usage summary."""
        if self.enabled and self.reporter:
            self.reporter.llm_summary(tech, news, synthesis, verify)

    def emit(self, message: str) -> None:
        """
        Legacy method for backward compatibility.

        This method is deprecated and should not be used in new code.
        Use step_start/step_done/panel/llm_summary instead.
        """
        # No-op: old TRACE | format is no longer used
        pass
