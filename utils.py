from os import listdir
from os.path import isfile, join
import time


def benchmark(func):
    """
    A benchmark tool
    """
    def function_timer(*args, **kwargs):
        start = time.time()
        value = func(*args, **kwargs)
        end = time.time()
        runtime = end - start
        print(
            f"`{func.__name__}` took {runtime} seconds"
        )
        return value
    return function_timer
