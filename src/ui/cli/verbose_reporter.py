from rich.console import Console
from rich.panel import Panel


class RichVerboseReporter:
    """
    Rich-based implementation of VerboseReporter for console output.

    Provides human-readable progress updates and formatted panels
    during pipeline execution in verbose mode.
    """

    def __init__(self, console: Console) -> None:
        self.console = console

    def step_start(self, text: str) -> None:
        self.console.print(f"[cyan]→[/cyan] {text}")

    def step_done(self, text: str) -> None:
        self.console.print(f"[green]✓[/green] {text}")

    def panel(self, title: str, body: str) -> None:
        self.console.print()
        self.console.print(Panel(body, title=title, border_style="blue"))
        self.console.print()

    def llm_summary(
        self,
        tech: str,
        news: str,
        synthesis: str,
        verify: str,
    ) -> None:
        summary_text = f"tech={tech} news={news} synthesis={synthesis} verify={verify}"
        self.console.print(f"[dim]LLM Summary:[/dim] {summary_text}")
