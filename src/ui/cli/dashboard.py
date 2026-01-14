from rich.console import Console
from rich.panel import Panel

from src.core.models.recommendation import Recommendation


class Dashboard:
    def __init__(self, console: Console) -> None:
        self.console = console

    def show_header(self) -> None:
        header_text = (
            "[bold cyan]Trading Research Assistant[/bold cyan]\n[dim]MVP - Demo Only[/dim]"
        )
        self.console.print(Panel(header_text, border_style="cyan"))

    def show_latest_run(
        self,
        symbol: str,
        rec: Recommendation | None,
        error: str | None,
    ) -> None:
        if error:
            error_panel = Panel(
                f"[red]Error: {error}[/red]",
                title=f"Latest Run - {symbol}",
                border_style="red",
            )
            self.console.print(error_panel)
        elif rec:
            success_panel = Panel(
                f"Action: [bold]{rec.action}[/bold]\nConfidence: {rec.confidence:.2%}",
                title=f"Latest Run - {symbol}",
                border_style="green",
            )
            self.console.print(success_panel)
        else:
            no_data_panel = Panel(
                "[dim]No recommendation available[/dim]",
                title=f"Latest Run - {symbol}",
                border_style="dim",
            )
            self.console.print(no_data_panel)
