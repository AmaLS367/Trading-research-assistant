from src.agents.prompts.technical_prompts import get_technical_system_prompt
from src.core.models.timeframe import Timeframe
from src.core.ports.llm_provider import LlmProvider
from src.features.snapshots.feature_snapshot import FeatureSnapshot


class TechnicalAnalyst:
    def __init__(self, llm_provider: LlmProvider) -> None:
        self.llm_provider = llm_provider

    def _symbol_to_display(self, symbol: str) -> str:
        symbol_upper = symbol.upper().strip()
        if len(symbol_upper) == 6:
            return f"{symbol_upper[:3]}/{symbol_upper[3:]}"
        return symbol_upper

    def _apply_output_guard(self, text: str, symbol: str, display_symbol: str) -> str:
        text_upper = text.upper()
        display_symbol_upper = display_symbol.upper()

        if display_symbol_upper in text_upper:
            return text

        other_pairs = [
            ("EUR/USD", "EURUSD"),
            ("GBP/USD", "GBPUSD"),
            ("USD/JPY", "USDJPY"),
            ("EURUSD", "EURUSD"),
            ("GBPUSD", "GBPUSD"),
            ("USDJPY", "USDJPY"),
        ]

        found_other_pair = False
        for pair_display, pair_ticker in other_pairs:
            if (pair_display in text_upper or pair_ticker in text_upper) and symbol.upper() != pair_ticker:
                found_other_pair = True
                break

        if found_other_pair:
            guard_prefix = f"Analysis scope: {display_symbol}. Note: model mentioned other instruments; ignore those references.\n\n"
            guarded_text = guard_prefix + text

            if symbol.upper() != "EURUSD":
                guarded_text = guarded_text.replace("EUR/USD", display_symbol)
                guarded_text = guarded_text.replace("eur/usd", display_symbol.lower())
            if symbol.upper() != "GBPUSD":
                guarded_text = guarded_text.replace("GBP/USD", display_symbol)
                guarded_text = guarded_text.replace("gbp/usd", display_symbol.lower())
            if symbol.upper() != "USDJPY":
                guarded_text = guarded_text.replace("USD/JPY", display_symbol)
                guarded_text = guarded_text.replace("usd/jpy", display_symbol.lower())

            return guarded_text

        return text

    def analyze(self, snapshot: FeatureSnapshot, symbol: str, timeframe: Timeframe) -> str:
        display_symbol = self._symbol_to_display(symbol)
        system_prompt = get_technical_system_prompt(display_symbol, timeframe.value)
        user_prompt = snapshot.to_markdown()

        technical_view = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        guarded_view = self._apply_output_guard(technical_view, symbol, display_symbol)

        return guarded_view
