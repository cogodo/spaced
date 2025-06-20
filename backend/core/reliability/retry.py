import time
import random
import asyncio
from typing import Callable, Any, Optional, Type, Union, Tuple
from dataclasses import dataclass
from functools import wraps

from core.monitoring.logger import get_logger
from core.monitoring.metrics import increment_counter, observe_histogram

logger = get_logger("retry")


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
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


def exponential_backoff(attempt: int, 
                       base_delay: float = 1.0, 
                       max_delay: float = 60.0,
                       exponential_base: float = 2.0,
                       jitter: bool = True) -> float:
    """
    Calculate exponential backoff delay
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Exponential growth factor
        jitter: Whether to add random jitter
    
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        # Add random jitter (±25%)
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay)  # Ensure non-negative
    
    return delay


def retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        config: Retry configuration
    
    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return _execute_with_retry(func, config, *args, **kwargs)
        return wrapper
    
    return decorator


def _execute_with_retry(func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
    """Execute function with retry logic"""
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            
            # Success - record metrics
            duration = time.time() - start_time
            observe_histogram("retry_function_duration_seconds", duration,
                            {"function": func.__name__, "attempt": str(attempt + 1)})
            
            if attempt > 0:
                logger.info(f"Function '{func.__name__}' succeeded on attempt {attempt + 1}",
                           function=func.__name__,
                           attempt=attempt + 1,
                           duration=duration)
                
                increment_counter("retry_success_after_failure",
                                {"function": func.__name__, "attempt": str(attempt + 1)})
            
            return result
            
        except config.retryable_exceptions as e:
            last_exception = e
            
            # Record failure
            increment_counter("retry_attempt_failed",
                            {"function": func.__name__, "attempt": str(attempt + 1)})
            
            if attempt < config.max_attempts - 1:
                # Calculate delay and sleep
                delay = exponential_backoff(
                    attempt,
                    config.base_delay,
                    config.max_delay,
                    config.exponential_base,
                    config.jitter
                )
                
                logger.warning(f"Function '{func.__name__}' failed on attempt {attempt + 1}, "
                             f"retrying in {delay:.2f}s",
                             function=func.__name__,
                             attempt=attempt + 1,
                             max_attempts=config.max_attempts,
                             delay=delay,
                             error_type=type(e).__name__,
                             error_message=str(e))
                
                time.sleep(delay)
            else:
                # Final attempt failed
                logger.error(f"Function '{func.__name__}' failed after {config.max_attempts} attempts",
                           function=func.__name__,
                           max_attempts=config.max_attempts,
                           error_type=type(e).__name__,
                           error_message=str(e))
                
                increment_counter("retry_exhausted",
                                {"function": func.__name__})
        
        except Exception as e:
            # Non-retryable exception
            logger.error(f"Function '{func.__name__}' failed with non-retryable exception",
                       function=func.__name__,
                       attempt=attempt + 1,
                       error_type=type(e).__name__,
                       error_message=str(e))
            
            increment_counter("retry_non_retryable_error",
                            {"function": func.__name__})
            raise
    
    # All attempts exhausted
    raise RetryExhaustedError(config.max_attempts, last_exception)


# Async versions
async def async_exponential_backoff(attempt: int, 
                                  base_delay: float = 1.0, 
                                  max_delay: float = 60.0,
                                  exponential_base: float = 2.0,
                                  jitter: bool = True) -> None:
    """Async version of exponential backoff"""
    delay = exponential_backoff(attempt, base_delay, max_delay, exponential_base, jitter)
    await asyncio.sleep(delay)


def async_retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying async functions with exponential backoff
    
    Args:
        config: Retry configuration
    
    Returns:
        Decorated async function
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await _async_execute_with_retry(func, config, *args, **kwargs)
        return wrapper
    
    return decorator


async def _async_execute_with_retry(func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
    """Execute async function with retry logic"""
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            start_time = time.time()
            
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - record metrics
            duration = time.time() - start_time
            observe_histogram("async_retry_function_duration_seconds", duration,
                            {"function": func.__name__, "attempt": str(attempt + 1)})
            
            if attempt > 0:
                logger.info(f"Async function '{func.__name__}' succeeded on attempt {attempt + 1}",
                           function=func.__name__,
                           attempt=attempt + 1,
                           duration=duration)
                
                increment_counter("async_retry_success_after_failure",
                                {"function": func.__name__, "attempt": str(attempt + 1)})
            
            return result
            
        except config.retryable_exceptions as e:
            last_exception = e
            
            # Record failure
            increment_counter("async_retry_attempt_failed",
                            {"function": func.__name__, "attempt": str(attempt + 1)})
            
            if attempt < config.max_attempts - 1:
                # Calculate delay and sleep
                delay = exponential_backoff(
                    attempt,
                    config.base_delay,
                    config.max_delay,
                    config.exponential_base,
                    config.jitter
                )
                
                logger.warning(f"Async function '{func.__name__}' failed on attempt {attempt + 1}, "
                             f"retrying in {delay:.2f}s",
                             function=func.__name__,
                             attempt=attempt + 1,
                             max_attempts=config.max_attempts,
                             delay=delay,
                             error_type=type(e).__name__,
                             error_message=str(e))
                
                await asyncio.sleep(delay)
            else:
                # Final attempt failed
                logger.error(f"Async function '{func.__name__}' failed after {config.max_attempts} attempts",
                           function=func.__name__,
                           max_attempts=config.max_attempts,
                           error_type=type(e).__name__,
                           error_message=str(e))
                
                increment_counter("async_retry_exhausted",
                                {"function": func.__name__})
        
        except Exception as e:
            # Non-retryable exception
            logger.error(f"Async function '{func.__name__}' failed with non-retryable exception",
                       function=func.__name__,
                       attempt=attempt + 1,
                       error_type=type(e).__name__,
                       error_message=str(e))
            
            increment_counter("async_retry_non_retryable_error",
                            {"function": func.__name__})
            raise
    
    # All attempts exhausted
    raise RetryExhaustedError(config.max_attempts, last_exception)


# Context manager for manual retry logic
class RetryContext:
    """Context manager for manual retry logic"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.attempt = 0
        self.last_exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.config.retryable_exceptions):
            self.last_exception = exc_val
            self.attempt += 1
            
            if self.attempt < self.config.max_attempts:
                delay = exponential_backoff(
                    self.attempt - 1,
                    self.config.base_delay,
                    self.config.max_delay,
                    self.config.exponential_base,
                    self.config.jitter
                )
                
                logger.warning(f"Retry context: attempt {self.attempt} failed, "
                             f"retrying in {delay:.2f}s",
                             attempt=self.attempt,
                             max_attempts=self.config.max_attempts,
                             delay=delay,
                             error_type=exc_type.__name__)
                
                time.sleep(delay)
                return True  # Suppress exception and continue
        
        return False  # Let exception propagate
    
    def should_retry(self) -> bool:
        """Check if we should continue retrying"""
        return self.attempt < self.config.max_attempts
    
    def raise_if_exhausted(self):
        """Raise RetryExhaustedError if all attempts are exhausted"""
        if self.attempt >= self.config.max_attempts and self.last_exception:
            raise RetryExhaustedError(self.attempt, self.last_exception) 