from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class JobResult(Generic[T]):
    ok: bool
    value: T | None
    error: str
