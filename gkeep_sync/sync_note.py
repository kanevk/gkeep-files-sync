import os
import hashlib
import json
import requests

from .utils import benchmark, traverse_files, DEFAULT_CONFIG_PATH

SYNC_LABEL = 'autosync'
FILE_EXTENSION = 'md'


class GkeepSyncAPI:
    def __init__(self, keep):
        config = json.load(open(DEFAULT_CONFIG_PATH))
        config['notes_root'] = os.path.expanduser(config['notes_root'])

        self.config = config
        self.keep = keep

    def create_note(self, title, text):
        print(f"Creating a note {title}")
        newNote = self.keep.createNote(title, text)
        label = self.keep.findLabel(SYNC_LABEL)
        newNote.labels.add(label)

        return newNote

    def find_note(self, title):
        label = self.keep.findLabel(SYNC_LABEL)
        gnotes = list(self.keep.find(labels=[label], func=lambda note: note.title == title))

        if len(gnotes) > 1:
            raise Exception(f'Too many notes match the title: {title}')
        return (gnotes[0] if len(gnotes) == 1 else None)

    def file_to_note_tuple(self, path):
        relative_path = path.replace(self.config['notes_root'], '')[1:]
        title = relative_path.replace(f".{FILE_EXTENSION}", '')

        print(f"title {title}")

        with open(path, 'r') as f: text = f.read()

        return {'path': path, 'title': title, 'text': text}

    def hash_equal(self, text_a, text_b):
        hash_a = hashlib.md5(text_a.encode('utf-8')).hexdigest()
        hash_b = hashlib.md5(text_b.encode('utf-8')).hexdigest()

        return hash_a == hash_b

    @benchmark
    def login(self):
        if not os.path.exists('.state.json'):
            self.keep.resume(self.config['email'], self.config['token'])

            # save state
            with open('.state.json', 'w') as state_file:
                json.dump(self.keep.dump(), state_file)
        else:
            with open('.state.json', 'r') as state_file:
                self.keep.resume(self.config['email'], self.config['token'], state=json.load(state_file))

    @benchmark
    def sync_up(self):
        if not self.check_connection():
            return

        try:
            self.keep.sync()
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            print("Error during syncing occurred")

    @benchmark
    def sync_down(self):
        if not self.check_connection():
            return

        try:
            self.keep.sync()
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            print("Error during syncing occurred")
            return

        remote_notes = list(self.keep.find(labels=[self.keep.findLabel(SYNC_LABEL)]))

        for note in remote_notes:
            if not note.title:
                continue

            path = f"{self.config['notes_root']}/{note.title}.{FILE_EXTENSION}"

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
                if not self.hash_equal(file.read(), note.text):
                    file.write(note.text)

    @benchmark
    def upload_new_notes(self):
        all_paths = traverse_files(self.config['notes_root'])

        file_note_states = list(
            map(
                self.file_to_note_tuple,
                filter(lambda path: path.endswith(f".{FILE_EXTENSION}"), all_paths)
            )
        )
        new_notes_count = 0

        for file_note_state in file_note_states:
            if self.find_note(file_note_state['title']):
                continue

            new_notes_count += 1
            self.create_note(file_note_state['title'], file_note_state['text'])

        print(f"Uploading {new_notes_count} new notes")
        print('syncing...')
        # This doesn't use sync_up() because we want to fail if there is network issue
        self.keep.sync()

    def check_connection(self, host='http://google.com'):
        try:
            requests.get(host, timeout=1)
            print("Internet connection present")
            return True
        except requests.exceptions.ConnectionError:
            print("No internet connection")
            return False


    @benchmark
    def run(self, note_path):
        note_data = self.file_to_note_tuple(note_path)
        note = self.find_note(note_data['title'])

        if note is None:
            note = self.create_note(note_data['title'], note_data['text'])

            print('syncing...')
            self.sync_up()
        elif not self.hash_equal(note.text, note_data['text']):
            note.text = note_data['text']

            print('syncing...')
            self.sync_up()
        else:
            print('No changes found.')
