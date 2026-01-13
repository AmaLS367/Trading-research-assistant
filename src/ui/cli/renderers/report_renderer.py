from rich.console import Console
from rich.table import Table


class ReportRenderer:
    def __init__(self, console: Console) -> None:
        self.console = console

    def render_daily_stats(self, table: Table) -> None:
        self.console.print(table)
