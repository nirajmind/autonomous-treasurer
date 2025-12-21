"""Retry logic with exponential backoff"""

import asyncio
import random
from typing import Callable, TypeVar, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryConfig:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter"""
        delay = min(self.initial_delay * (self.exponential_base ** attempt), self.max_delay)
        if self.jitter:
            delay *= (0.5 + random.random())
        return delay


async def retry_async(
    func: Callable,
    *args,
    config: RetryConfig = None,
    retriable_exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry async function with exponential backoff
    
    Example:
        await retry_async(
            fetch_from_rpc,
            config=RetryConfig(max_attempts=3),
            retriable_exceptions=(RPCTimeoutError, ConnectionError)
        )
    """
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            logger.debug(f"Attempt {attempt + 1}/{config.max_attempts} for {func.__name__}")
            return await func(*args, **kwargs)
        
        except retriable_exceptions as e:
            last_exception = e
            if attempt < config.max_attempts - 1:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"{func.__name__} failed (attempt {attempt + 1}), "
                    f"retrying in {delay:.2f}s: {str(e)}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"{func.__name__} failed after {config.max_attempts} attempts: {str(e)}"
                )
    
    raise last_exception


def retry_async_decorator(
    config: RetryConfig = None,
    retriable_exceptions: tuple = (Exception,)
):
    """Decorator for async functions"""
    config = config or RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                func,
                *args,
                config=config,
                retriable_exceptions=retriable_exceptions,
                **kwargs
            )
        return wrapper
    return decorator