import time
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional, Tuple, Type

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.monitoring.logger import get_logger
from core.monitoring.metrics import increment_counter, observe_histogram

logger = get_logger("retry")


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_attempts: int = 3
    base_delay: float = 1.0  # Corresponds to 'multiplier' in tenacity
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True  # Jitter is default in tenacity's wait_exponential
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted"""

    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(
            f"Retry exhausted after {attempts} attempts. "
            f"Last error: {type(last_exception).__name__}: {last_exception}"
        )


def _create_before_sleep_callback(func_name: str, max_attempts: int):
    """Factory to create a before_sleep callback for logging."""

    def log_before_sleep(retry_state):
        """Callback to log before sleeping."""
        attempt = retry_state.attempt_number
        delay = retry_state.next_action.sleep
        error_type = type(retry_state.outcome.exception()).__name__
        error_message = str(retry_state.outcome.exception())

        logger.warning(
            f"Function '{func_name}' failed on attempt {attempt}, "
            f"retrying in {delay:.2f}s",
            function=func_name,
            attempt=attempt,
            max_attempts=max_attempts,
            delay=delay,
            error_type=error_type,
            error_message=error_message,
        )

    return log_before_sleep


def retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying functions with exponential backoff using tenacity.
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        # A wrapper to handle metrics and logging around tenacity
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            # Configure tenacity retry decorator
            tenacity_decorator = retry(
                stop=stop_after_attempt(config.max_attempts),
                wait=wait_exponential(
                    multiplier=config.base_delay,
                    max=config.max_delay,
                    exp_base=config.exponential_base,
                ),
                retry=retry_if_exception_type(config.retryable_exceptions),
                before_sleep=_create_before_sleep_callback(
                    func_name, config.max_attempts
                ),
                reraise=True,  # Reraise the last exception
            )

            try:
                # Apply the decorator
                decorated_func = tenacity_decorator(func)
                result = decorated_func(*args, **kwargs)

                # Success metrics
                duration = time.time() - start_time
                attempt = decorated_func.retry.statistics.get("attempt_number", 1)
                observe_histogram(
                    "retry_function_duration_seconds",
                    duration,
                    {"function": func_name, "attempt": str(attempt)},
                )
                if attempt > 1:
                    increment_counter(
                        "retry_success_after_failure",
                        {"function": func_name, "attempt": str(attempt)},
                    )
                return result

            except RetryError as e:
                increment_counter("retry_exhausted", {"function": func_name})
                raise RetryExhaustedError(
                    config.max_attempts, e.last_attempt.exception()
                ) from e

            except Exception as e:
                # Non-retryable exception
                increment_counter("retry_non_retryable_error", {"function": func_name})
                logger.error(
                    f"Function '{func_name}' failed with non-retryable exception",
                    function=func_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        return wrapper

    return decorator


def async_retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying async functions with exponential backoff using tenacity.
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        # A wrapper to handle metrics and logging around tenacity
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            # Configure tenacity async retry decorator
            tenacity_decorator = retry(
                stop=stop_after_attempt(config.max_attempts),
                wait=wait_exponential(
                    multiplier=config.base_delay,
                    max=config.max_delay,
                    exp_base=config.exponential_base,
                ),
                retry=retry_if_exception_type(config.retryable_exceptions),
                before_sleep=_create_before_sleep_callback(
                    func_name, config.max_attempts
                ),
                reraise=True,
            )

            try:
                # Apply the decorator
                decorated_func = tenacity_decorator(func)
                result = await decorated_func(*args, **kwargs)

                # Success metrics
                duration = time.time() - start_time
                attempt = decorated_func.retry.statistics.get("attempt_number", 1)
                observe_histogram(
                    "async_retry_function_duration_seconds",
                    duration,
                    {"function": func_name, "attempt": str(attempt)},
                )
                if attempt > 1:
                    increment_counter(
                        "async_retry_success_after_failure",
                        {"function": func_name, "attempt": str(attempt)},
                    )
                return result

            except RetryError as e:
                increment_counter("async_retry_exhausted", {"function": func_name})
                raise RetryExhaustedError(
                    config.max_attempts, e.last_attempt.exception()
                ) from e

            except Exception as e:
                # Non-retryable exception
                increment_counter(
                    "async_retry_non_retryable_error", {"function": func_name}
                )
                logger.error(
                    f"Async function '{func_name}' failed with non-retryable exception",
                    function=func_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        return wrapper

    return decorator


# The custom context manager is removed as 'tenacity' provides a more robust way
# of handling retries via decorators. If manual retry logic is strictly needed,
# tenacity's 'Retrying' object can be used in a loop.
