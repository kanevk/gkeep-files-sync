from os import listdir
from os.path import isfile, join, expanduser
import time

CONFIG_FOLDER_PATH = join(expanduser("~"), ".gkeep-sync")
DEFAULT_CONFIG_PATH = join(CONFIG_FOLDER_PATH, "config.json")
DUMPED_STATE_PATH = join(CONFIG_FOLDER_PATH, "state.json")


def traverse_files(path):
    files = []
    for f in listdir(path):
        if isfile(join(path, f)):
            files.append(join(path, f))
        else:
            files += traverse_files(join(path, f))

    return files


def benchmark(func):
    """
    A benchmark tool
    """
    def function_timer(*args, **kwargs):
        start = time.time()
        value = func(*args, **kwargs)

        print(f"{func.__name__} took {time.time() - start} seconds")

        return value
    return function_timer
