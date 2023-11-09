import logging
import functools

logging = logging.getLogger(__name__)


## @method cache_results
## @brief Cache results of a function
## @param func: function to cache
## @return wrapper: wrapper function
def cache_results(func):
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        if args in cache:
            logging.info("cache hit for %s", func.__name__)
            return cache[args]
        logging.info("cache miss for %s", func.__name__)
        result = func(*args)
        cache[args] = result
        return result

    return wrapper
