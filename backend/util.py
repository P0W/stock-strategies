"""
This module provides a decorator for caching function results.
"""

import functools
import logging
import sqlite3
import redis
import os
import json

logging = logging.getLogger(__name__)

## Read from the environment variable
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    redis_client.ping()  # Check the connection
    logging.info("redis connection ok")
except redis.exceptions.ConnectionError:
    logging.warning("redis connection error %s:%s", REDIS_HOST, REDIS_PORT)
    redis_client = None


def cache_results(func):
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        global redis_client
        ## strip off object address
        try:
            key = f"{func.__name__}:{str(args[1:])}"
        except IndexError:
            key = f"{func.__name__}:"
        if redis_client is not None:
            try:
                result_str = redis_client.get(key)
                if result_str is not None and len(result_str) > 0:
                    result = json.loads(result_str) # Convert to dict
                    logging.info("redis cache hit for %s", key)
                    return result
                else:
                    logging.warn("redis cache miss for %s | %s", key, result_str)
            except redis.exceptions.ConnectionError:
                redis_client = None
            except json.decoder.JSONDecodeError as e:
                logging.error("JSONDecodeError error %s | %s", key, result_str)
                logging.error(e)
                redis_client = None

        if redis_client is None:
            if args in cache:
                logging.info("in-memory cache hit for %s", key)
                return cache[args]
            logging.info("in-memory cache miss for %s", key)
            result = func(*args)
            cache[args] = result
            return result

        logging.info("redis cache miss for %s", key)
        result = func(*args)
        try:
            result_str = json.dumps(result) # Convert to string
            redis_client.set(key, result_str, ex=3600)  # Cache for 1 hour
            logging.warn("redis cached %s for 1 hour", key)
        except redis.exceptions.ConnectionError:
            redis_client = None
        return result

    return wrapper


def create_users_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def ensure_users_table_exists(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not os.path.isfile('users.db'):
            create_users_table()
        return func(*args, **kwargs)
    return wrapper
