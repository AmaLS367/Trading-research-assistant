from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol

from src.core.models.journal_entry import JournalEntry
from src.core.models.outcome import Outcome
from src.core.models.rationale import Rationale
from src.core.models.recommendation import Recommendation
from src.core.models.run import Run


class RunsRepositoryPort(Protocol):
    def create(self, run: Run) -> int:
        ...

    def update_run(
        self,
        run_id: int,
        status: str,
        end_time: datetime,
        error_message: str | None,
    ) -> None:
        ...

    def get_by_id(self, run_id: int) -> Run | None:
        ...


class RecommendationsRepositoryPort(Protocol):
    def save(self, recommendation: Recommendation) -> int:
        ...

    def get_latest(self) -> Recommendation | None:
        ...


class RationalesRepositoryPort(Protocol):
    def save(self, rationale: Rationale) -> int:
        ...

    def get_by_run_id(self, run_id: int) -> list[Rationale]:
        ...


class JournalRepositoryPort(Protocol):
    def save(self, entry: JournalEntry) -> int:
        ...

    def get_latest_by_symbol(self, symbol: str) -> JournalEntry | None:
        ...

    def get_latest(self) -> JournalEntry | None:
        ...


class OutcomesRepositoryPort(Protocol):
    def save(self, outcome: Outcome) -> int:
        ...

    def get_all_with_details(self) -> list[dict[str, str | int | None]]:
        ...


class Storage(ABC):
    @property
    @abstractmethod
    def runs(self) -> RunsRepositoryPort:
        pass

    @property
    @abstractmethod
    def recommendations(self) -> RecommendationsRepositoryPort:
        pass

    @property
    @abstractmethod
    def rationales(self) -> RationalesRepositoryPort:
        pass

    @property
    @abstractmethod
    def journal(self) -> JournalRepositoryPort:
        pass

    @property
    @abstractmethod
    def outcomes(self) -> OutcomesRepositoryPort:
        pass
