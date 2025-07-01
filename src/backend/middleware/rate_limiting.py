import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from core.monitoring.logger import get_logger
from core.monitoring.metrics import increment_counter

logger = get_logger("rate_limiting")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    enable_user_limits: bool = True
    enable_ip_limits: bool = True
    enable_endpoint_limits: bool = True


class RateLimitBucket:
    """Token bucket for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize rate limit bucket

        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.RLock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if rate limited
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def time_until_available(self, tokens: int = 1) -> float:
        """Calculate time until tokens are available"""
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                return 0.0

            needed_tokens = tokens - self.tokens
            return needed_tokens / self.refill_rate

    def get_info(self) -> Dict[str, float]:
        """Get bucket status information"""
        with self._lock:
            self._refill()
            return {
                "tokens": self.tokens,
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
                "usage_percent": ((self.capacity - self.tokens) / self.capacity) * 100,
            }


class RateLimiter:
    """Rate limiter with multiple bucket strategies"""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()

        # Buckets for different rate limit types
        self.ip_buckets: Dict[str, RateLimitBucket] = {}
        self.user_buckets: Dict[str, RateLimitBucket] = {}
        self.endpoint_buckets: Dict[str, RateLimitBucket] = {}

        # Request tracking
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Cleanup tracking
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

        # Thread safety
        self._lock = threading.RLock()

        logger.info(
            "Rate limiter initialized",
            requests_per_minute=self.config.requests_per_minute,
            requests_per_hour=self.config.requests_per_hour,
            burst_size=self.config.burst_size,
        )

    def check_rate_limit(
        self,
        ip_address: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request should be rate limited

        Args:
            ip_address: Client IP address
            user_id: User identifier (if authenticated)
            endpoint: API endpoint path

        Returns:
            Tuple of (allowed, limit_info)
        """
        with self._lock:
            self._cleanup_old_buckets()

            limit_info = {
                "ip_limited": False,
                "user_limited": False,
                "endpoint_limited": False,
                "retry_after": 0,
            }

            max_retry_after = 0

            # Check IP rate limit
            if self.config.enable_ip_limits and ip_address:
                ip_bucket = self._get_ip_bucket(ip_address)
                if not ip_bucket.consume():
                    limit_info["ip_limited"] = True
                    retry_after = ip_bucket.time_until_available()
                    max_retry_after = max(max_retry_after, retry_after)

                    logger.warning(
                        "IP rate limit exceeded",
                        ip_address=ip_address,
                        retry_after=retry_after,
                    )

                    increment_counter("rate_limit_exceeded", {"type": "ip"})

            # Check user rate limit
            if self.config.enable_user_limits and user_id:
                user_bucket = self._get_user_bucket(user_id)
                if not user_bucket.consume():
                    limit_info["user_limited"] = True
                    retry_after = user_bucket.time_until_available()
                    max_retry_after = max(max_retry_after, retry_after)

                    logger.warning(
                        "User rate limit exceeded",
                        user_id=user_id,
                        retry_after=retry_after,
                    )

                    increment_counter("rate_limit_exceeded", {"type": "user"})

            # Check endpoint rate limit
            if self.config.enable_endpoint_limits and endpoint:
                endpoint_bucket = self._get_endpoint_bucket(endpoint)
                if not endpoint_bucket.consume():
                    limit_info["endpoint_limited"] = True
                    retry_after = endpoint_bucket.time_until_available()
                    max_retry_after = max(max_retry_after, retry_after)

                    logger.warning(
                        "Endpoint rate limit exceeded",
                        endpoint=endpoint,
                        retry_after=retry_after,
                    )

                    increment_counter("rate_limit_exceeded", {"type": "endpoint"})

            # Record request
            self._record_request(ip_address, user_id, endpoint)

            limit_info["retry_after"] = max_retry_after
            is_allowed = not any(
                [
                    limit_info["ip_limited"],
                    limit_info["user_limited"],
                    limit_info["endpoint_limited"],
                ]
            )

            if not is_allowed:
                increment_counter("requests_rate_limited")
            else:
                increment_counter("requests_allowed")

            return is_allowed, limit_info

    def _get_ip_bucket(self, ip_address: str) -> RateLimitBucket:
        """Get or create rate limit bucket for IP address"""
        if ip_address not in self.ip_buckets:
            self.ip_buckets[ip_address] = RateLimitBucket(
                capacity=self.config.burst_size,
                refill_rate=self.config.requests_per_minute / 60.0,
            )
        return self.ip_buckets[ip_address]

    def _get_user_bucket(self, user_id: str) -> RateLimitBucket:
        """Get or create rate limit bucket for user"""
        if user_id not in self.user_buckets:
            # Users get higher limits than IPs
            self.user_buckets[user_id] = RateLimitBucket(
                capacity=self.config.burst_size * 2,
                refill_rate=self.config.requests_per_minute * 1.5 / 60.0,
            )
        return self.user_buckets[user_id]

    def _get_endpoint_bucket(self, endpoint: str) -> RateLimitBucket:
        """Get or create rate limit bucket for endpoint"""
        if endpoint not in self.endpoint_buckets:
            # Different endpoints may have different limits
            # For now, use same limits but could be configurable
            self.endpoint_buckets[endpoint] = RateLimitBucket(
                capacity=self.config.burst_size * 10,  # Higher capacity for endpoints
                refill_rate=self.config.requests_per_minute * 5 / 60.0,  # Higher rate
            )
        return self.endpoint_buckets[endpoint]

    def _record_request(
        self, ip_address: str, user_id: Optional[str], endpoint: Optional[str]
    ):
        """Record request for analytics"""
        now = time.time()

        # Record in history
        key = f"ip:{ip_address}"
        self.request_history[key].append(now)

        if user_id:
            key = f"user:{user_id}"
            self.request_history[key].append(now)

        if endpoint:
            key = f"endpoint:{endpoint}"
            self.request_history[key].append(now)

    def _cleanup_old_buckets(self):
        """Clean up unused buckets to prevent memory leaks"""
        now = time.time()

        if now - self.last_cleanup < self.cleanup_interval:
            return

        self.last_cleanup = now

        # Remove buckets that haven't been used in a while
        cutoff_time = now - 3600  # 1 hour

        # Clean IP buckets
        inactive_ips = [
            ip
            for ip, bucket in self.ip_buckets.items()
            if bucket.last_refill < cutoff_time
        ]
        for ip in inactive_ips:
            del self.ip_buckets[ip]

        # Clean user buckets
        inactive_users = [
            user
            for user, bucket in self.user_buckets.items()
            if bucket.last_refill < cutoff_time
        ]
        for user in inactive_users:
            del self.user_buckets[user]

        # Clean endpoint buckets (keep these longer)
        endpoint_cutoff = now - 7200  # 2 hours
        inactive_endpoints = [
            endpoint
            for endpoint, bucket in self.endpoint_buckets.items()
            if bucket.last_refill < endpoint_cutoff
        ]
        for endpoint in inactive_endpoints:
            del self.endpoint_buckets[endpoint]

        logger.debug(
            "Rate limiter cleanup completed",
            removed_ip_buckets=len(inactive_ips),
            removed_user_buckets=len(inactive_users),
            removed_endpoint_buckets=len(inactive_endpoints),
        )

    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        with self._lock:
            return {
                "active_ip_buckets": len(self.ip_buckets),
                "active_user_buckets": len(self.user_buckets),
                "active_endpoint_buckets": len(self.endpoint_buckets),
                "config": {
                    "requests_per_minute": self.config.requests_per_minute,
                    "requests_per_hour": self.config.requests_per_hour,
                    "burst_size": self.config.burst_size,
                },
            }

    def get_bucket_info(
        self, bucket_type: str, identifier: str
    ) -> Optional[Dict[str, any]]:
        """Get information about a specific bucket"""
        with self._lock:
            bucket = None

            if bucket_type == "ip" and identifier in self.ip_buckets:
                bucket = self.ip_buckets[identifier]
            elif bucket_type == "user" and identifier in self.user_buckets:
                bucket = self.user_buckets[identifier]
            elif bucket_type == "endpoint" and identifier in self.endpoint_buckets:
                bucket = self.endpoint_buckets[identifier]

            if bucket:
                return bucket.get_info()
            return None


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        self.rate_limiter = rate_limiter or RateLimiter()

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""

        # Extract client information
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        endpoint = str(request.url.path)

        # Check rate limits
        allowed, limit_info = self.rate_limiter.check_rate_limit(
            ip_address=client_ip, user_id=user_id, endpoint=endpoint
        )

        if not allowed:
            # Rate limited - return 429 response
            headers = {
                "Retry-After": str(int(limit_info["retry_after"]) + 1),
                "X-RateLimit-Limit": str(self.rate_limiter.config.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + limit_info["retry_after"])),
            }

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": limit_info["retry_after"],
                    "limits": {
                        "ip_limited": limit_info["ip_limited"],
                        "user_limited": limit_info["user_limited"],
                        "endpoint_limited": limit_info["endpoint_limited"],
                    },
                },
                headers=headers,
            )

        # Request allowed - add rate limit headers and continue
        response = await call_next(request)

        # Add rate limit headers to response
        if hasattr(response, "headers"):
            response.headers["X-RateLimit-Limit"] = str(
                self.rate_limiter.config.requests_per_minute
            )

            # Calculate remaining tokens (approximation)
            bucket_info = self.rate_limiter.get_bucket_info("ip", client_ip)
            if bucket_info:
                response.headers["X-RateLimit-Remaining"] = str(
                    int(bucket_info["tokens"])
                )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        # Fall back to client host
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (if authenticated)"""
        # This would typically be extracted from JWT token or session
        # For now, check if user info is available in request state
        if hasattr(request.state, "user_id"):
            return request.state.user_id

        # Could also check authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT here
            # For now, we'll return None
            pass

        return None


# Global rate limiter instance
_global_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _global_rate_limiter
