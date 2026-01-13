from abc import ABC, abstractmethod


class BaseImporter(ABC):
    @abstractmethod
    def import_data(self) -> None:
        pass
