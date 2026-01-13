from src.core.ports.storage import (
    JournalRepositoryPort,
    OutcomesRepositoryPort,
    RationalesRepositoryPort,
    RecommendationsRepositoryPort,
    RunsRepositoryPort,
    Storage,
)
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.journal_repository import JournalRepository
from src.storage.sqlite.repositories.outcomes_repository import OutcomesRepository
from src.storage.sqlite.repositories.rationales_repository import RationalesRepository
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository
from src.storage.sqlite.repositories.runs_repository import RunsRepository


class SqliteStorage(Storage):
    def __init__(self, db: DBConnection) -> None:
        self._db = db
        self._runs_repo = RunsRepository(db)
        self._recommendations_repo = RecommendationsRepository(db)
        self._rationales_repo = RationalesRepository(db)
        self._journal_repo = JournalRepository(db)
        self._outcomes_repo = OutcomesRepository(db)

    @property
    def runs(self) -> RunsRepositoryPort:
        return self._runs_repo

    @property
    def recommendations(self) -> RecommendationsRepositoryPort:
        return self._recommendations_repo

    @property
    def rationales(self) -> RationalesRepositoryPort:
        return self._rationales_repo

    @property
    def journal(self) -> JournalRepositoryPort:
        return self._journal_repo

    @property
    def outcomes(self) -> OutcomesRepositoryPort:
        return self._outcomes_repo
