# Purpose: In-memory rate limiting for login attempts.
# Security: Throttles failed authentication attempts per username + IP to mitigate credential brute force.

import threading
import time

from app.config import settings

_lock = threading.Lock()
# Mapping of (username, ip) -> list of timestamp floats
_failed_attempts: dict[tuple[str, str], list[float]] = {}


def _cleanup(now: float, window_seconds: float) -> None:
    """Purge stale failed attempts."""
    for key in list(_failed_attempts.keys()):
        valid_times = [t for t in _failed_attempts[key] if now - t < window_seconds]
        if valid_times:
            _failed_attempts[key] = valid_times
        else:
            del _failed_attempts[key]


def is_rate_limited(username: str, ip: str) -> bool:
    """Check if the given username + IP pair has exceeded the allowed failed attempts."""
    key = (username.strip().lower(), ip.strip())
    now = time.time()
    window_seconds = settings.LOGIN_RATE_LIMIT_WINDOW_MINUTES * 60

    with _lock:
        _cleanup(now, window_seconds)
        attempts = _failed_attempts.get(key, [])
        return len(attempts) >= settings.LOGIN_RATE_LIMIT_ATTEMPTS


def record_failed_attempt(username: str, ip: str) -> None:
    """Record a failed login attempt for the username + IP."""
    key = (username.strip().lower(), ip.strip())
    now = time.time()
    window_seconds = settings.LOGIN_RATE_LIMIT_WINDOW_MINUTES * 60

    with _lock:
        _cleanup(now, window_seconds)
        if key not in _failed_attempts:
            _failed_attempts[key] = []
        _failed_attempts[key].append(now)


def clear_failed_attempts(username: str, ip: str) -> None:
    """Reset failed attempts upon successful login."""
    key = (username.strip().lower(), ip.strip())
    with _lock:
        if key in _failed_attempts:
            del _failed_attempts[key]


def reset_all_rate_limits() -> None:
    """Clear all rate limit state (useful in testing)."""
    with _lock:
        _failed_attempts.clear()
