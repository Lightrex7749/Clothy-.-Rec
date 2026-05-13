"""Simple in-memory rate limiting for API endpoints."""
from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Deque, Dict

from fastapi import HTTPException, Request


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_sec: int) -> bool:
        now = monotonic()
        with self._lock:
            queue = self._hits[key]
            while queue and queue[0] <= now - window_sec:
                queue.popleft()
            if len(queue) >= limit:
                return False
            queue.append(now)
            return True


_limiter = SlidingWindowRateLimiter()


def rate_limit(limit: int, bucket: str, window_sec: int):
    def _dependency(request: Request) -> None:
        if limit <= 0:
            return
        client = request.client.host if request.client else "unknown"
        key = f"{bucket}:{client}"
        if not _limiter.allow(key, limit, window_sec):
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again soon.")

    return _dependency
