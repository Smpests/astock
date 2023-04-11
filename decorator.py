from functools import wraps
import logging
import time

logging.basicConfig(level=logging.INFO)


def cost(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        res = func(*args, **kwargs)
        logging.info(f"{func.__name__} cost {time.time() - start_time}s")
        return res
    return wrapper
