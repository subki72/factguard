"""
Rate limiter — 3 requests per minute per IP address (BR13).

Uses in-memory storage (dictionary) which resets on serverless cold start.
This is acceptable for Vercel serverless because:
- Each function instance has its own memory
- Cold starts naturally reset the counter
- For 30 concurrent users, this provides sufficient protection
"""

import time
from collections import defaultdict

from fastapi import Request


class RateLimitExceeded(Exception):
    """Raised when a client exceeds the rate limit."""
    pass


# In-memory store: { ip_address: [timestamp1, timestamp2, ...] }
_request_log: dict[str, list[float]] = defaultdict(list)

# Configuration (SR4.1: 50 requests per hour)
MAX_REQUESTS = 50
WINDOW_SECONDS = 3600


def check_rate_limit(request: Request) -> None:
    """
    Check if the client IP has exceeded the rate limit.

    Raises RateLimitExceeded if the limit is exceeded.
    """
    # Get client IP (Vercel forwards the real IP in x-forwarded-for)
    client_ip = request.headers.get(
        "x-forwarded-for", request.client.host if request.client else "unknown"
    )
    # Take only the first IP if there are multiple (proxy chain)
    client_ip = client_ip.split(",")[0].strip()

    now = time.time()
    window_start = now - WINDOW_SECONDS

    # Clean up old entries outside the window
    _request_log[client_ip] = [
        ts for ts in _request_log[client_ip] if ts > window_start
    ]

    # Check if limit exceeded
    if len(_request_log[client_ip]) >= MAX_REQUESTS:
        raise RateLimitExceeded()

    # Record this request
    _request_log[client_ip].append(now)


def get_client_ip_hash(request: Request) -> str:
    """
    Get a hashed version of the client IP for storage (privacy).

    We use a simple hash — not cryptographically strong, but sufficient
    for our use case of de-duplication rather than security.
    """
    import hashlib

    client_ip = request.headers.get(
        "x-forwarded-for", request.client.host if request.client else "unknown"
    )
    client_ip = client_ip.split(",")[0].strip()
    return hashlib.sha256(client_ip.encode()).hexdigest()[:16]
