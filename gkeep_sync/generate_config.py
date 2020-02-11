import json
import sys
from os import path

from .utils import DEFAULT_CONFIG_PATH

import gkeepapi


def generate_config():
    if len(sys.argv) != 4:
        print("Please provide email, password, notes_root in the exactly same order")
        exit(1)

    config = {
        "email": sys.argv[1],
        "password": sys.argv[2],
        "notes_root": sys.argv[3]
    }

    if not path.exists(DEFAULT_CONFIG_PATH):
        open(DEFAULT_CONFIG_PATH, 'x').close()

    keep = gkeepapi.Keep()
    keep.login(config['email'], config['password'])

    config['token'] = keep.getMasterToken()

    json.dump(config, open(DEFAULT_CONFIG_PATH, 'w'), indent=2)

    print(f"You can find the config on: {DEFAULT_CONFIG_PATH}")


if __name__ == "__main__":
    generate_config()
