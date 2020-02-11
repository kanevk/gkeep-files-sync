import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

import gkeepapi

from . import sync_note


SYNC_DOWN_INTERVAL = 60  # seconds


class EventHandler(LoggingEventHandler):
    def __init__(self, sync_api):
        self.sync_api = sync_api

    def on_modified(self, event):
        super(EventHandler, self).on_modified(event)

        if not event.is_directory:
            self.sync_api.run(event.src_path)


def start_server():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    keep = gkeepapi.Keep()

    sync_api = sync_note.GkeepSyncAPI(keep)
    sync_api.login()

    sync_api.upload_new_notes()

    observer = Observer()
    observer.schedule(EventHandler(sync_api), sync_api.config['notes_root'], recursive=True)
    observer.start()

    try:
        while True:
            sync_api.sync_down()

            time.sleep(SYNC_DOWN_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    start_server()
