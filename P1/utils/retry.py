# retry.py
import time
import logging
from typing import Union, Tuple, Type
from functools import wraps

logger = logging.getLogger(__name__)


def retry_on_exception(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
):
    """重试装饰器，用于LLM调用等可能失败的操作"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Retry {attempt+1}/{max_retries} after error: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None  # pragma: no cover

        return wrapper

    return decorator
