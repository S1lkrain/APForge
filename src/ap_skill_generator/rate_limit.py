from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from fastapi import HTTPException, Request


@dataclass
class RateLimiter:
    """Simple in-memory sliding-window rate limiter keyed by client IP."""

    limits: dict[str, tuple[int, int]] = field(default_factory=dict)
    _hits: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def check(self, *, client_key: str, route_key: str) -> None:
        if route_key not in self.limits:
            return
        max_requests, window_seconds = self.limits[route_key]
        now = time.monotonic()
        bucket_key = f"{client_key}:{route_key}"
        hits = self._hits[bucket_key]
        cutoff = now - window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        hits.append(now)

    def reset(self) -> None:
        self._hits.clear()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
