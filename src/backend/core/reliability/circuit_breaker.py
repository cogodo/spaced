import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

from core.monitoring.logger import get_logger
from core.monitoring.metrics import increment_counter

logger = get_logger("circuit_breaker")


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5  # Number of failures to trigger open state
    recovery_timeout: float = 60.0  # Seconds to wait before testing recovery
    success_threshold: int = 3  # Successful calls needed to close from half-open
    timeout: float = 30.0  # Request timeout in seconds
    monitored_exceptions: tuple = (Exception,)  # Exceptions that count as failures


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""

    pass


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures"""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker

        Args:
            name: Unique name for this circuit breaker
            config: Configuration parameters
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None

        # Thread safety
        self._lock = threading.RLock()

        # Metrics tracking
        self.call_history = deque(maxlen=100)

        logger.info(
            f"Circuit breaker '{name}' initialized",
            failure_threshold=self.config.failure_threshold,
            recovery_timeout=self.config.recovery_timeout,
        )

    def __call__(self, func: Callable) -> Callable:
        """Decorator interface for circuit breaker"""

        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self._lock:
            self._update_state()

            if self.state == CircuitBreakerState.OPEN:
                self._record_call("rejected", 0)
                increment_counter(
                    "circuit_breaker_calls_rejected", {"circuit_breaker": self.name}
                )

                logger.warning(
                    f"Circuit breaker '{self.name}' is OPEN, rejecting call",
                    state=self.state.value,
                    failure_count=self.failure_count,
                )

                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service temporarily unavailable."
                )

            # Allow call through
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Success
                duration = time.time() - start_time
                self._record_success(duration)
                self._record_call("success", duration)

                return result

            except self.config.monitored_exceptions as e:
                # Failure
                duration = time.time() - start_time
                self._record_failure(duration)
                self._record_call("failure", duration)

                logger.warning(
                    f"Circuit breaker '{self.name}' recorded failure",
                    exception_type=type(e).__name__,
                    failure_count=self.failure_count,
                    state=self.state.value,
                )

                raise

    def _update_state(self):
        """Update circuit breaker state based on current conditions"""
        now = time.time()

        if self.state == CircuitBreakerState.OPEN:
            # Check if we should transition to half-open
            if (
                self.last_failure_time
                and now - self.last_failure_time > self.config.recovery_timeout
            ):
                self._transition_to_half_open()

        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Check if we should close (enough successes)
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()

    def _record_success(self, duration: float):
        """Record a successful call"""
        self.last_success_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

        increment_counter(
            "circuit_breaker_calls_success", {"circuit_breaker": self.name}
        )

        logger.debug(
            f"Circuit breaker '{self.name}' recorded success",
            duration=duration,
            state=self.state.value,
            success_count=self.success_count,
        )

    def _record_failure(self, duration: float):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # Reset success count on failure
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count = 0
            self._transition_to_open()
        elif (
            self.state == CircuitBreakerState.CLOSED
            and self.failure_count >= self.config.failure_threshold
        ):
            self._transition_to_open()

        increment_counter(
            "circuit_breaker_calls_failure", {"circuit_breaker": self.name}
        )

    def _record_call(self, result: str, duration: float):
        """Record call in history for metrics"""
        self.call_history.append(
            {
                "timestamp": datetime.utcnow(),
                "result": result,
                "duration": duration,
                "state": self.state.value,
            }
        )

    def _transition_to_open(self):
        """Transition circuit breaker to OPEN state"""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN

        logger.warning(
            f"Circuit breaker '{self.name}' transitioned to OPEN",
            old_state=old_state.value,
            new_state=self.state.value,
            failure_count=self.failure_count,
        )

        increment_counter(
            "circuit_breaker_state_changes",
            {"circuit_breaker": self.name, "new_state": "open"},
        )

    def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state"""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.success_count = 0

        logger.info(
            f"Circuit breaker '{self.name}' transitioned to HALF_OPEN",
            old_state=old_state.value,
            new_state=self.state.value,
        )

        increment_counter(
            "circuit_breaker_state_changes",
            {"circuit_breaker": self.name, "new_state": "half_open"},
        )

    def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state"""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0

        logger.info(
            f"Circuit breaker '{self.name}' transitioned to CLOSED",
            old_state=old_state.value,
            new_state=self.state.value,
        )

        increment_counter(
            "circuit_breaker_state_changes",
            {"circuit_breaker": self.name, "new_state": "closed"},
        )

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self._lock:
            # Calculate metrics from call history
            recent_calls = [
                c for c in self.call_history if time.time() - c["timestamp"] <= 60
            ]
            failure_rate = self._calculate_failure_rate(recent_calls)

            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time,
                "last_success_time": self.last_success_time,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout,
                },
                "recent_metrics": {
                    "failure_rate_percent": round(failure_rate, 2),
                },
            }

    def reset(self):
        """Reset circuit breaker to initial state"""
        with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.last_success_time = None

            logger.info(f"Circuit breaker '{self.name}' reset to initial state")

    def force_open(self):
        """Force circuit breaker to OPEN state (for testing/maintenance)"""
        with self._lock:
            self._transition_to_open()

            logger.warning(f"Circuit breaker '{self.name}' forced to OPEN state")

    def force_closed(self):
        """Force circuit breaker to CLOSED state (for testing/recovery)"""
        with self._lock:
            self._transition_to_closed()

            logger.info(f"Circuit breaker '{self.name}' forced to CLOSED state")


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_circuit_breakers_lock = threading.RLock()


def get_circuit_breaker(
    name: str, config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create a circuit breaker by name"""
    with _circuit_breakers_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name, config)
        return _circuit_breakers[name]


def list_circuit_breakers() -> Dict[str, Dict[str, Any]]:
    """Get stats for all circuit breakers"""
    with _circuit_breakers_lock:
        return {name: cb.get_status() for name, cb in _circuit_breakers.items()}


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator for applying circuit breaker to a function"""
    cb = get_circuit_breaker(name, config)
    return cb
