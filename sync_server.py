import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import sync_note


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
    path = sys.argv[1] if len(sys.argv) > 1 else '.'

    keep = sync_note.gkeepapi.Keep()

    sync_note.login(keep)

    event_handler = EventHandler(keep)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print("After observer start")

    timer = 0
    try:
        while True:
            if timer % 60 == 0:
                sync_note.sync_with_remote(keep)
            time.sleep(1)
            timer += 1
    except KeyboardInterrupt:
        observer.stop()
    # Check this out
    observer.join()
