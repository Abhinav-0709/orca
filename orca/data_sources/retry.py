"""Bounded retry and exponential backoff helpers for live data sources."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import httpx


T = TypeVar("T")

RETRYABLE_HTTP_STATUS_CODES = frozenset({408, 425, 429, 500, 502, 503, 504})
RETRYABLE_EXCEPTIONS = (httpx.RequestError, httpx.TimeoutException)


class RetryableHTTPStatusError(RuntimeError):
    """Raised internally when an HTTP response should be retried."""

    def __init__(self, status_code: int, url: str) -> None:
        super().__init__(f"Retryable HTTP status {status_code} from {url}")
        self.status_code = status_code
        self.url = url


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.25,
    max_delay_seconds: float = 2.0,
    retryable_exceptions: tuple[type[BaseException], ...] = (
        *RETRYABLE_EXCEPTIONS,
        RetryableHTTPStatusError,
    ),
    sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
    on_retry: Callable[[int, float, BaseException], None] | None = None,
) -> T:
    """Run an async operation with bounded exponential backoff.

    ``max_attempts`` includes the first call.  The helper never retries an
    exception outside ``retryable_exceptions`` and re-raises the final
    exception so callers can switch to their existing operational fallback.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if base_delay_seconds < 0 or max_delay_seconds < 0:
        raise ValueError("retry delays cannot be negative")

    attempt = 1
    while True:
        try:
            return await operation()
        except retryable_exceptions as exc:
            if attempt >= max_attempts:
                raise

            delay = min(max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)))
            if on_retry is not None:
                on_retry(attempt, delay, exc)
            await sleep(delay)
            attempt += 1


async def http_get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.25,
    max_delay_seconds: float = 2.0,
    on_retry: Callable[[int, float, BaseException], None] | None = None,
    **request_kwargs: Any,
) -> httpx.Response:
    """GET a URL, retrying transient network and HTTP failures."""

    async def operation() -> httpx.Response:
        response = await client.get(url, **request_kwargs)
        if response.status_code in RETRYABLE_HTTP_STATUS_CODES:
            raise RetryableHTTPStatusError(response.status_code, url)
        return response

    return await retry_async(
        operation,
        max_attempts=max_attempts,
        base_delay_seconds=base_delay_seconds,
        max_delay_seconds=max_delay_seconds,
        on_retry=on_retry,
    )
