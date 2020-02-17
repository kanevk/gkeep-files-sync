import time
import logging
import json
import hashlib
import os
import atexit

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

from .sync_api import SyncAPI
from .utils import CONFIG_FOLDER_PATH, DEFAULT_CONFIG_PATH


SYNC_DOWN_INTERVAL = 60  # seconds


class EventHandler(LoggingEventHandler):
    def __init__(self, sync_api):
        self.sync_api = sync_api

    def on_modified(self, event):
        super(EventHandler, self).on_modified(event)

        if not event.is_directory:
            self.sync_api.upsert_note(event.src_path)


def start_server():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    config = build_config()

    guard_for_duplicate_servers(config)

    sync_api = SyncAPI.login(config)
    sync_api.upload_new_notes()

    observer = Observer()
    observer.schedule(EventHandler(sync_api), config['notes_root__absolute'], recursive=True)
    observer.start()

    try:
        while True:
            sync_api.sync_down()

            time.sleep(SYNC_DOWN_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


def guard_for_duplicate_servers(config):
    notes_root_id = hashlib.md5(config['notes_root__absolute'].encode('utf-8')).hexdigest()
    lock_file_path = os.path.join(CONFIG_FOLDER_PATH, f".lock-{notes_root_id}")

    if os.path.exists(lock_file_path):
        print(f"""
        A GKeep server is already running for notes root \"{config['notes_root__absolute']}\"
        """)

        # TODO: Find a more suitable status
        exit(126)
    else:
        atexit.register(lambda: os.remove(lock_file_path))
        open(lock_file_path, 'x').close()


def build_config():
    config_path = os.environ.get('GKEEP_CONFIG_PATH', DEFAULT_CONFIG_PATH)
    config = json.load(open(config_path))
    config['notes_root__absolute'] = os.path.expanduser(config['notes_root'])

    return config


if __name__ == "__main__":
    start_server()
