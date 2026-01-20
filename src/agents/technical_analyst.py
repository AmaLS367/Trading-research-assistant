from __future__ import annotations

from typing import TYPE_CHECKING

from src.agents.prompts.technical_prompts import get_technical_system_prompt
from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.core.models.timeframe import Timeframe
from src.core.ports.llm_tasks import TASK_TECH_ANALYSIS
from src.features.snapshots.feature_snapshot import FeatureSnapshot
from src.llm.providers.llm_router import LlmRouter
from src.utils.json_helpers import extract_json_from_text, try_parse_json
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.core.models.llm import LlmResponse

logger = get_logger(__name__)


class TechnicalAnalyst:
    def __init__(self, llm_router: LlmRouter) -> None:
        self.llm_router = llm_router

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
            if (
                pair_display in text_upper or pair_ticker in text_upper
            ) and symbol.upper() != pair_ticker:
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

    def analyze(
        self, snapshot: FeatureSnapshot, symbol: str, timeframe: Timeframe
    ) -> tuple[str, LlmResponse]:
        display_symbol = self._symbol_to_display(symbol)
        system_prompt = get_technical_system_prompt(display_symbol, timeframe.value)
        user_prompt = snapshot.to_markdown()

        logger.debug(
            f"Tech analysis prompt built: symbol={symbol}, timeframe={timeframe.value}, "
            f"system_prompt_chars={len(system_prompt)}, user_prompt_chars={len(user_prompt)}"
        )

        llm_response = self.llm_router.generate(
            task=TASK_TECH_ANALYSIS,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        raw_text = llm_response.text
        extracted_json_text = extract_json_from_text(raw_text)

        technical_result: TechnicalAnalysisResult | None = None
        if extracted_json_text is not None:
            parsed = try_parse_json(extracted_json_text)
            if parsed is not None:
                try:
                    technical_result = TechnicalAnalysisResult.model_validate(parsed)
                except ValueError:
                    technical_result = None

        if technical_result is None:
            no_trade_flags = ["PARSING_FAILED"]
            if llm_response.error:
                no_trade_flags.append("LLM_ERROR")

            technical_result = TechnicalAnalysisResult(
                bias="NEUTRAL",
                confidence=0.0,
                evidence=[],
                contradictions=[],
                setup_type=None,
                no_trade_flags=no_trade_flags,
            )

        guarded_view = technical_result.model_dump_json()

        # Extract key info from response for logging
        action_bias = None
        if "CALL" in guarded_view.upper() or "BUY" in guarded_view.upper():
            action_bias = "CALL"
        elif "PUT" in guarded_view.upper() or "SELL" in guarded_view.upper():
            action_bias = "PUT"

        logger.debug(
            f"Tech analysis result parsed: action_bias={action_bias}, "
            f"response_chars={len(guarded_view)}, "
            f"rationale_summary={guarded_view[:100]}..."
            if len(guarded_view) > 100
            else f"rationale={guarded_view}"
        )

        return guarded_view, llm_response
