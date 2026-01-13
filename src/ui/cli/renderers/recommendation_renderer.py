from rich.panel import Panel

from src.core.models.rationale import Rationale
from src.core.models.recommendation import Recommendation


class RecommendationRenderer:
    @staticmethod
    def render(rec: Recommendation, rationale: Rationale | None) -> Panel:
        action = rec.action.upper()
        if action == "CALL":
            border_style = "green"
            action_style = "[bold green]CALL[/bold green]"
        elif action == "PUT":
            border_style = "red"
            action_style = "[bold red]PUT[/bold red]"
        else:
            border_style = "yellow"
            action_style = "[bold yellow]WAIT[/bold yellow]"

        content_parts = [
            f"Symbol: {rec.symbol}",
            f"Timeframe: {rec.timeframe.value}",
            f"Action: {action_style}",
            f"Confidence: {rec.confidence:.2%}",
            "",
            f"Brief: {rec.brief}",
        ]

        if rationale:
            content_parts.append("")
            content_parts.append("Rationale:")
            content_parts.append(rationale.content)

        content = "\n".join(content_parts)
        return Panel(content, title="Recommendation", border_style=border_style)
