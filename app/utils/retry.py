"""Retry utility for external provider calls."""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, TypeVar

_log = logging.getLogger("viral_videos")

T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    *,
    retryable: tuple[type[Exception], ...],
    max_attempts: int = 3,
    initial_delay_sec: float = 1.0,
) -> T:
    """Call ``fn`` up to ``max_attempts`` times, retrying on ``retryable`` exceptions.

    Uses exponential backoff: delay doubles after each failed attempt.
    The final exception is re-raised if all attempts fail.

    Args:
        fn: Zero-argument callable to invoke.
        retryable: Tuple of exception types that allow a retry.
        max_attempts: Maximum number of total attempts (>= 1).
        initial_delay_sec: Seconds to wait before the second attempt; doubles thereafter.

    Returns:
        The return value of the first successful ``fn()`` call.

    Raises:
        The last raised retryable exception when all attempts are exhausted.
        Any non-retryable exception is propagated immediately without retrying.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retryable as exc:
            last_exc = exc
            if attempt == max_attempts:
                _log.warning(
                    "All %d attempt(s) failed: %s", max_attempts, exc
                )
                break
            delay = initial_delay_sec * (2 ** (attempt - 1))
            _log.warning(
                "Retryable error (attempt %d/%d): %s — retrying in %.1fs",
                attempt, max_attempts, exc, delay,
            )
            time.sleep(delay)

    raise last_exc  # type: ignore[misc]
