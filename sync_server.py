import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import sync_note

SYNC_DOWN_INTERVAL = 60  # seconds


class EventHandler(LoggingEventHandler):
    def __init__(self, keep):
        self._keep = keep

    def on_modified(self, event):
        super(EventHandler, self).on_modified(event)
        #
        if not event.is_directory:
            sync_note.run(self._keep, event.src_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    keep = sync_note.gkeepapi.Keep()

    sync_note.login(keep)

    sync_note.upload_new_notes(keep)

    event_handler = EventHandler(keep)
    observer = Observer()
    observer.schedule(event_handler, sync_note.NOTES_ROOT, recursive=True)
    observer.start()
    print("After observer start")

    timer = 0
    try:
        while True:
            if timer % SYNC_DOWN_INTERVAL == 0:
                sync_note.sync_down(keep)

            time.sleep(1)
            timer += 1
    except KeyboardInterrupt:
        observer.stop()
    # Check this out
    observer.join()
