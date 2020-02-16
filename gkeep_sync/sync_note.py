import os
import hashlib
import json
import requests

import gkeepapi

from .utils import benchmark, traverse_files, DEFAULT_CONFIG_PATH


SYNC_LABEL = 'autosync'
FILE_EXTENSION = 'md'


class GkeepSyncAPI:
    @staticmethod
    def login():
        keep = gkeepapi.Keep()
        config = json.load(open(DEFAULT_CONFIG_PATH))

        if not os.path.exists('.state.json'):
            keep.resume(config['email'], config['token'])

            # save state
            with open('.state.json', 'w') as state_file:
                json.dump(keep.dump(), state_file)
        else:
            with open('.state.json', 'r') as state_file:
                keep.resume(config['email'], config['token'], state=json.load(state_file))

        return GkeepSyncAPI(keep=keep, config=config)

    def __init__(self, keep, config):
        self.keep = keep
        self.sync_label = keep.findLabel(SYNC_LABEL)
        self.notes_root = os.path.expanduser(config['notes_root'])

    @benchmark
    def upsert_note(self, note_path):
        note_data = self._file_to_note_data(note_path)
        note = self._find_note(note_data['title'])

        if note is None:
            note = self._create_note(note_data['title'], note_data['text'])

            print('syncing...')
            self._sync_up()
        elif not self._hash_equal(note.text, note_data['text']):
            note.text = note_data['text']

            print('syncing...')
            self._sync_up()
        else:
            print('No changes found.')

    @benchmark
    def upload_new_notes(self):
        all_paths = traverse_files(self.notes_root)

        file_note_states = list(
            map(
                self._file_to_note_data,
                filter(lambda path: path.endswith(f".{FILE_EXTENSION}"), all_paths)
            )
        )
        new_notes_count = 0

        for file_note_state in file_note_states:
            if self._find_note(file_note_state['title']):
                continue

            new_notes_count += 1
            self._create_note(file_note_state['title'], file_note_state['text'])

        print(f"Uploading {new_notes_count} new notes")
        print('syncing...')
        # This doesn't use _sync_up() because we want to fail if there is network issue
        self.keep.sync()

    @benchmark
    def sync_down(self):
        if not self._check_connection():
            return

        try:
            self.keep.sync()
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            print("Error during syncing occurred")
            return

        remote_notes = list(self.keep.find(labels=[self.sync_label]))

        for note in remote_notes:
            if not note.title:
                continue

            path = f"{self.notes_root}/{note.title}.{FILE_EXTENSION}"

            # CREATE
            if not os.path.exists(path):
                # When creating/updating a note in the remote it takes a while to write it's title.
                # While you're writing on the local server a sync down(every N seconds) may be scheduled and
                # it'll create a file with the current version of the title which will be incomplete.
                # During the next sync down a new file will be created for the same note with full title.
                # This is a problem, because the *UPDATE* functionality its based on comparison of titles.
                #
                # In order to make it work for *CREATION*, we assume that when the user writes the title of a note,
                # the content stays empty.
                if not note.text:
                    continue

                open(path, 'x').close()

            # UPDATE
            with open(path, 'w+') as file:
                if not self._hash_equal(file.read(), note.text):
                    file.write(note.text)

    def _create_note(self, title, text):
        print(f"Creating a note {title}")
        newNote = self.keep.createNote(title, text)
        newNote.labels.add(self.sync_label)

        return newNote

    def _find_note(self, title):
        gnotes = list(self.keep.find(labels=[self.sync_label], func=lambda note: note.title == title))

        if len(gnotes) > 1:
            raise Exception(f'Too many notes match the title: {title}')

        return (gnotes[0] if gnotes else None)

    def _file_to_note_data(self, path):
        relative_path = path.replace(self.notes_root, '')[1:]
        title = relative_path.replace(f".{FILE_EXTENSION}", '')

        print(f"title {title}")

        with open(path, 'r') as f:
            text = f.read()

        return {'path': path, 'title': title, 'text': text}

    @benchmark
    def _sync_up(self):
        if not self._check_connection():
            return

        try:
            self.keep.sync()
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            print("Error during syncing occurred")

    def _hash_equal(self, text_a, text_b):
        hash_a = hashlib.md5(text_a.encode('utf-8')).hexdigest()
        hash_b = hashlib.md5(text_b.encode('utf-8')).hexdigest()

        return hash_a == hash_b

    def _check_connection(self, host='http://google.com'):
        try:
            requests.get(host, timeout=1)
            print("Internet connection present")
            return True
        except requests.exceptions.ConnectionError:
            print("No internet connection")
            return False
