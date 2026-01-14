from collections.abc import Callable
from typing import Any, TypeVar, cast

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

T = TypeVar("T")


def retry_network_call(
    func: Callable[..., T] | None = None,
    max_attempts: int = 3,
    min_wait: float = 2.0,
    max_wait: float = 10.0,
) -> Any:
    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        retry_decorator = retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(
                (httpx.TransportError, httpx.TimeoutException, httpx.NetworkError, TimeoutError)
            ),
        )
        return cast(Callable[..., T], retry_decorator(f))

    if func is None:
        return decorator
    return decorator(func)
