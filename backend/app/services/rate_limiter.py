# Rate Limiting Service - CPX-SEC
# Provides in-memory rate limiting for API endpoints
# Uses sliding window algorithm

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import threading


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an endpoint"""
    requests_per_window: int  # Max requests allowed in window
    window_seconds: int        # Window size in seconds
    burst_allowance: int = 0  # Additional burst requests allowed


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    Thread-safe for concurrent access.
    """

    # Default rate limits
    DEFAULT_LIMITS = {
        # Auth endpoints - strict limits
        "/api/auth/login": RateLimitConfig(requests_per_window=5, window_seconds=60),
        "/api/auth/register": RateLimitConfig(requests_per_window=3, window_seconds=300),

        # Game endpoints - moderate limits
        "/api/games/": RateLimitConfig(requests_per_window=30, window_seconds=60),
        "/api/games": RateLimitConfig(requests_per_window=30, window_seconds=60),

        # Order endpoints - higher limits for gameplay
        "/api/orders/": RateLimitConfig(requests_per_window=60, window_seconds=60),
        "/api/turn/commit": RateLimitConfig(requests_per_window=20, window_seconds=60),

        # Report endpoints - moderate limits
        "/api/reports/": RateLimitConfig(requests_per_window=20, window_seconds=60),

        # Parse order - can be called frequently
        "/api/parse-order": RateLimitConfig(requests_per_window=30, window_seconds=60),

        # Internal endpoints - strict limits
        "/api/internal/": RateLimitConfig(requests_per_window=10, window_seconds=60),
    }

    def __init__(self, custom_limits: Optional[Dict[str, RateLimitConfig]] = None):
        self.limits = {**self.DEFAULT_LIMITS}
        if custom_limits:
            self.limits.update(custom_limits)

        # Store request timestamps per endpoint per client
        # Structure: { "client_id:endpoint": [timestamp1, timestamp2, ...] }
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _get_client_key(self, client_id: str, endpoint: str) -> str:
        """Generate unique key for client+endpoint combination"""
        return f"{client_id}:{endpoint}"

    def _clean_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests outside the current window"""
        current_time = time.time()
        cutoff = current_time - window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check_rate_limit(self, client_id: str, endpoint: str) -> tuple[bool, Optional[Dict]]:
        """
        Check if request is within rate limit.

        Args:
            client_id: Unique identifier for the client (IP, user ID, etc.)
            endpoint: API endpoint path

        Returns:
            Tuple of (is_allowed, rate_limit_info)
            - is_allowed: True if request is allowed
            - rate_limit_info: Dict with limit details if limited, None otherwise
        """
        # Find matching rate limit config
        config = self._find_matching_config(endpoint)

        with self._lock:
            key = self._get_client_key(client_id, endpoint)

            # Clean old requests outside window
            self._clean_old_requests(key, config.window_seconds)

            # Check current request count
            current_count = len(self._requests[key])
            max_allowed = config.requests_per_window + config.burst_allowance

            if current_count >= max_allowed:
                # Rate limited
                oldest_request = min(self._requests[key]) if self._requests[key] else time.time()
                retry_after = int(oldest_request + config.window_seconds - time.time()) + 1

                return False, {
                    "limit": config.requests_per_window,
                    "remaining": 0,
                    "reset": int(time.time() + config.window_seconds),
                    "retry_after": retry_after
                }

            # Add current request timestamp
            self._requests[key].append(time.time())

            remaining = max_allowed - current_count - 1
            return True, {
                "limit": config.requests_per_window,
                "remaining": max(0, remaining),
                "reset": int(time.time() + config.window_seconds),
                "retry_after": None
            }

    def _find_matching_config(self, endpoint: str) -> RateLimitConfig:
        """Find the most specific rate limit config for an endpoint"""
        # Try exact match first
        if endpoint in self.limits:
            return self.limits[endpoint]

        # Try prefix match
        for pattern, config in self.limits.items():
            if pattern.endswith("/") and endpoint.startswith(pattern):
                return config
            if endpoint.startswith(pattern.rstrip("/")):
                return config

        # Default fallback
        return RateLimitConfig(requests_per_window=60, window_seconds=60)

    def reset_client(self, client_id: str) -> None:
        """Reset rate limits for a specific client"""
        with self._lock:
            keys_to_remove = [k for k in self._requests.keys() if k.startswith(f"{client_id}:")]
            for key in keys_to_remove:
                del self._requests[key]

    def get_stats(self, client_id: str, endpoint: str) -> Dict:
        """Get current rate limit stats for a client+endpoint"""
        config = self._find_matching_config(endpoint)
        key = self._get_client_key(client_id, endpoint)

        with self._lock:
            self._clean_old_requests(key, config.window_seconds)
            current_count = len(self._requests[key])

            return {
                "current": current_count,
                "limit": config.requests_per_window,
                "burst": config.burst_allowance,
                "window_seconds": config.window_seconds,
                "remaining": max(0, config.requests_per_window + config.burst_allowance - current_count)
            }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the global rate limiter (for testing)"""
    global _rate_limiter
    _rate_limiter = None
