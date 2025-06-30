import asyncio
import signal
import time
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional

from core.monitoring.logger import get_logger
from core.monitoring.metrics import increment_counter

logger = get_logger("timeouts")


@dataclass
class TimeoutConfig:
    """Configuration for timeout behavior"""

    timeout_seconds: float = 30.0
    raise_on_timeout: bool = True


class TimeoutError(Exception):
    """Raised when an operation times out"""

    def __init__(self, timeout_seconds: float, operation: str = "operation"):
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        super().__init__(f"{operation} timed out after {timeout_seconds} seconds")


class TimeoutContext:
    """Context manager for timeout handling"""

    def __init__(self, timeout_seconds: float, operation: str = "operation"):
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        self.start_time = None
        self.timed_out = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time

            if duration >= self.timeout_seconds:
                self.timed_out = True
                logger.warning(
                    f"Operation '{self.operation}' timed out",
                    operation=self.operation,
                    duration=duration,
                    timeout=self.timeout_seconds,
                )

                increment_counter("operation_timeout", {"operation": self.operation})

    def check_timeout(self):
        """Check if operation has timed out and raise if configured"""
        if self.start_time:
            duration = time.time() - self.start_time
            if duration >= self.timeout_seconds:
                self.timed_out = True
                raise TimeoutError(self.timeout_seconds, self.operation)

    def remaining_time(self) -> float:
        """Get remaining time before timeout"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            return max(0, self.timeout_seconds - elapsed)
        return self.timeout_seconds


@contextmanager
def with_timeout(timeout_seconds: float, operation: str = "operation"):
    """Context manager for timeout handling"""
    context = TimeoutContext(timeout_seconds, operation)
    try:
        with context:
            yield context
    finally:
        if context.timed_out:
            raise TimeoutError(timeout_seconds, operation)


def timeout_decorator(timeout_seconds: float, operation: Optional[str] = None):
    """
    Decorator for adding timeout to functions

    Args:
        timeout_seconds: Maximum execution time
        operation: Operation name for logging (defaults to function name)
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                # For simple timeout without interruption
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if duration >= timeout_seconds:
                    logger.warning(
                        f"Function '{op_name}' exceeded timeout but completed",
                        function=func.__name__,
                        duration=duration,
                        timeout=timeout_seconds,
                    )

                    increment_counter("function_timeout_exceeded", {"function": func.__name__})

                return result

            except Exception as e:
                duration = time.time() - start_time

                if duration >= timeout_seconds:
                    logger.error(
                        f"Function '{op_name}' timed out and failed",
                        function=func.__name__,
                        duration=duration,
                        timeout=timeout_seconds,
                        error_type=type(e).__name__,
                    )

                    increment_counter("function_timeout_with_error", {"function": func.__name__})

                    # Convert to timeout error if it took too long
                    raise TimeoutError(timeout_seconds, op_name) from e

                raise

        return wrapper

    return decorator


# Async timeout functionality
async def async_with_timeout(coro, timeout_seconds: float, operation: str = "async_operation"):
    """
    Run async operation with timeout

    Args:
        coro: Coroutine to execute
        timeout_seconds: Maximum execution time
        operation: Operation name for logging

    Returns:
        Result of the coroutine

    Raises:
        TimeoutError: If operation times out
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout_seconds)
        return result

    except asyncio.TimeoutError as e:
        logger.warning(
            f"Async operation '{operation}' timed out",
            operation=operation,
            timeout=timeout_seconds,
        )

        increment_counter("async_operation_timeout", {"operation": operation})

        raise TimeoutError(timeout_seconds, operation) from e


def async_timeout_decorator(timeout_seconds: float, operation: Optional[str] = None):
    """
    Decorator for adding timeout to async functions

    Args:
        timeout_seconds: Maximum execution time
        operation: Operation name for logging (defaults to function name)
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    coro = func(*args, **kwargs)
                    result = await async_with_timeout(coro, timeout_seconds, op_name)
                else:
                    # Handle sync function in async context
                    result = func(*args, **kwargs)

                return result

            except TimeoutError:
                # Re-raise timeout errors
                raise
            except Exception as e:
                logger.error(
                    f"Async function '{op_name}' failed",
                    function=func.__name__,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        return wrapper

    return decorator


# Signal-based timeout (Unix only) - for operations that need hard interruption
class SignalTimeout:
    """Signal-based timeout for Unix systems"""

    def __init__(self, timeout_seconds: float, operation: str = "operation"):
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        self.old_handler = None

    def __enter__(self):
        # Set up signal handler
        def timeout_handler(signum, frame):
            raise TimeoutError(self.timeout_seconds, self.operation)

        self.old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.timeout_seconds))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up signal
        signal.alarm(0)
        if self.old_handler:
            signal.signal(signal.SIGALRM, self.old_handler)


def signal_timeout(timeout_seconds: float, operation: str = "operation"):
    """
    Context manager for signal-based timeout (Unix only)

    Note: This will interrupt the operation with SIGALRM
    Use with caution as it may leave resources in inconsistent state
    """
    return SignalTimeout(timeout_seconds, operation)


# Utility functions for timeout management
def calculate_timeout_with_buffer(base_timeout: float, buffer_percent: float = 10.0) -> float:
    """
    Calculate timeout with buffer

    Args:
        base_timeout: Base timeout in seconds
        buffer_percent: Buffer percentage to add

    Returns:
        Timeout with buffer added
    """
    buffer = base_timeout * (buffer_percent / 100.0)
    return base_timeout + buffer


def adaptive_timeout(
    previous_durations: list,
    multiplier: float = 1.5,
    min_timeout: float = 1.0,
    max_timeout: float = 300.0,
) -> float:
    """
    Calculate adaptive timeout based on previous operation durations

    Args:
        previous_durations: List of previous operation durations
        multiplier: Multiplier to apply to average duration
        min_timeout: Minimum timeout value
        max_timeout: Maximum timeout value

    Returns:
        Calculated timeout value
    """
    if not previous_durations:
        return min_timeout

    avg_duration = sum(previous_durations) / len(previous_durations)
    adaptive = avg_duration * multiplier

    return max(min_timeout, min(adaptive, max_timeout))
