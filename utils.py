import time
import functools
from logger import logger
from config import MAX_UPLOAD_RETRIES

def exponential_backoff(retries=MAX_UPLOAD_RETRIES, base_delay=2, exceptions=(Exception,)):
    """
    Decorator for exponential backoff retries.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries:
                        logger.warning(f"Attempt {attempt + 1}/{retries} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.error(f"All {retries} retries failed for {func.__name__}.")
            raise last_exception
        return wrapper
    return decorator
