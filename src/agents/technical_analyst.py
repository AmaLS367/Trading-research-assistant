from src.agents.prompts.technical_prompts import get_technical_system_prompt
from src.core.ports.llm_provider import LlmProvider
from src.features.snapshots.feature_snapshot import FeatureSnapshot


class TechnicalAnalyst:
    def __init__(self, llm_provider: LlmProvider) -> None:
        self.llm_provider = llm_provider

    def analyze(self, snapshot: FeatureSnapshot) -> str:
        system_prompt = get_technical_system_prompt()
        user_prompt = snapshot.to_markdown()

        technical_view = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return technical_view
