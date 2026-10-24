"""Tests for bounded live data-source retries."""

import pytest
import httpx

from orca.data_sources.retry import RetryableHTTPStatusError, http_get_with_retry, retry_async


@pytest.mark.asyncio
async def test_retry_async_retries_transient_failures_with_capped_backoff():
    attempts = 0
    delays: list[float] = []

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RetryableHTTPStatusError(503, "https://marine.example.test")
        return "ok"

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    result = await retry_async(
        operation,
        max_attempts=3,
        base_delay_seconds=0.1,
        max_delay_seconds=0.15,
        sleep=fake_sleep,
    )

    assert result == "ok"
    assert attempts == 3
    assert delays == [0.1, 0.15]


@pytest.mark.asyncio
async def test_retry_async_does_not_retry_non_transient_errors():
    attempts = 0

    async def operation() -> None:
        nonlocal attempts
        attempts += 1
        raise ValueError("invalid response shape")

    with pytest.raises(ValueError, match="invalid response shape"):
        await retry_async(operation, max_attempts=3, base_delay_seconds=0, sleep=lambda _: None)  # type: ignore[arg-type]

    assert attempts == 1


@pytest.mark.asyncio
async def test_http_get_with_retry_retries_transient_http_status():
    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def get(self, url: str, **kwargs):
            self.calls += 1
            status = 503 if self.calls == 1 else 200
            return httpx.Response(status, request=httpx.Request("GET", url))

    client = FakeClient()
    response = await http_get_with_retry(
        client,  # type: ignore[arg-type]
        "https://marine.example.test",
        max_attempts=2,
        base_delay_seconds=0,
        sleep=lambda _: _completed_sleep(),
    )

    assert response.status_code == 200
    assert client.calls == 2


async def _completed_sleep() -> None:
    return None
