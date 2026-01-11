import time
import sys
from functools import wraps

LOG_FILE = "scrape_errors.log"


def log_error(msg):
    line = f"[ERROR] {msg}\n"
    sys.stderr.write(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def with_retry(max_retries=3, backoff_seconds=5):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            delay = backoff_seconds
            for attempt in range(1, max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    log_error(f"{fn.__name__} failed (attempt {attempt}/{max_retries}): {e}")
                    if attempt == max_retries:
                        raise
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator
