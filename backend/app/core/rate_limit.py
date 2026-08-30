"""In-memory sliding-window rate limiter and login-lockout helper.

ponytail: process-local dict, fine for a single backend instance / dev / CI.
Swap for a Redis INCR+EXPIRE counter (REDIS_URL is already configured) before
running more than one backend replica, since counters won't be shared across
processes otherwise.
"""
import time
from collections import defaultdict

_hits: dict[str, list[float]] = defaultdict(list)


def reset_rate_limits() -> None:
    """Test-only helper — clears all counters between tests so one test's
    login attempts don't trip another's rate limit."""
    _hits.clear()


def check_rate_limit(key: str, *, limit: int, window_seconds: int = 60) -> bool:
    """Returns True if the call is allowed, False if the caller is over limit.
    Records the call as a hit only when allowed."""
    now = time.monotonic()
    window_start = now - window_seconds
    hits = [t for t in _hits[key] if t > window_start]
    if len(hits) >= limit:
        _hits[key] = hits
        return False
    hits.append(now)
    _hits[key] = hits
    return True
