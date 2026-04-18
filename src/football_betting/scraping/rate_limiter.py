"""
Token-bucket rate limiter for external API calls.

Blocks until a token is available. Conservative defaults (25s between
Sofascore requests) to avoid Cloudflare challenges.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass(slots=True)
class TokenBucketLimiter:
    """Thread-safe token-bucket rate limiter."""

    rate_per_second: float  # tokens added per second
    burst_capacity: int = 1  # max tokens stored
    _tokens: float = field(init=False, default=0.0)
    _last_refill: float = field(init=False, default_factory=time.monotonic)
    _lock: Lock = field(init=False, default_factory=Lock)

    def __post_init__(self) -> None:
        self._tokens = float(self.burst_capacity)

    def acquire(self, tokens: float = 1.0) -> float:
        """
        Block until `tokens` tokens are available; return wait time in seconds.
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return 0.0

            # How long until enough tokens?
            deficit = tokens - self._tokens
            wait = deficit / self.rate_per_second

        # Sleep OUTSIDE the lock to allow other threads to check
        time.sleep(wait)
        with self._lock:
            self._refill()
            self._tokens = max(0.0, self._tokens - tokens)
        return wait

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            float(self.burst_capacity),
            self._tokens + elapsed * self.rate_per_second,
        )
        self._last_refill = now

    @classmethod
    def from_delay(cls, delay_seconds: float, burst: int = 1) -> TokenBucketLimiter:
        """Construct from per-request delay (1/delay = rate)."""
        return cls(rate_per_second=1.0 / delay_seconds, burst_capacity=burst)
