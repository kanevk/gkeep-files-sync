import os
import hashlib
import sys
import json
import requests

import gkeepapi
import keyring

from utils import benchmark, traverse_files


CONFIG = json.load(open('.config.json'))
NOTES_ROOT = os.path.expanduser(CONFIG['notes_root'])
SYNC_LABEL = 'autosync'
FILE_EXTENSION = 'md'


def create_note(keep, title, text):
    print(f"Creating a note {title}")
    newNote = keep.createNote(title, text)
    label = keep.findLabel(SYNC_LABEL)
    newNote.labels.add(label)

    return newNote


def find_note(keep, title):
    label = keep.findLabel(SYNC_LABEL)
    gnotes = list(keep.find(labels=[label], func=lambda note: note.title == title))

    if len(gnotes) > 1:
        raise Exception(f'Too many notes match the title: {title}')
    return (gnotes[0] if len(gnotes) == 1 else None)


def file_to_note_tuple(path):
    relative_path = path.replace(NOTES_ROOT, '')[1:]
    title = relative_path.replace(f".{FILE_EXTENSION}", '')

    print(f"title {title}")

    with open(path, 'r') as f: text = f.read()

    return {'path': path, 'title': title, 'text': text}


def hash_equal(text_a, text_b):
    hash_a = hashlib.md5(text_a.encode('utf-8')).hexdigest()
    hash_b = hashlib.md5(text_b.encode('utf-8')).hexdigest()

    return hash_a == hash_b


@benchmark
def login(keep):
    if not os.path.exists('.state.json'):
        keep.resume(CONFIG['email'], CONFIG['token'])

        # save state
        with open('.state.json', 'w') as state_file:
            json.dump(keep.dump(), state_file)
    else:
        with open('.state.json', 'r') as state_file:
            keep.resume(CONFIG['email'], CONFIG['token'],
                        state=json.load(state_file))


@benchmark
def sync_up(keep):
    if not check_connection():
        return

    try:
        keep.sync()
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        print("Error during syncing occurred")


@benchmark
def sync_down(keep):
    if not check_connection():
        return

    try:
        keep.sync()
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        print("Error during syncing occurred")
        return

    remote_notes = list(keep.find(labels=[keep.findLabel(SYNC_LABEL)]))

    for note in remote_notes:
        if not note.title:
            continue

        path = f"{NOTES_ROOT}/{note.title}.{FILE_EXTENSION}"

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
        with open(path, 'r+') as file:
            if not hash_equal(file.read(), note.text):
                file.write(note.text)


@benchmark
def upload_new_notes(keep):
    all_paths = traverse_files(NOTES_ROOT)

    file_note_states = list(
        map(
            file_to_note_tuple,
            filter(lambda path: path.endswith(f".{FILE_EXTENSION}"), all_paths)
        )
    )
    new_notes_count = 0

    for file_note_state in file_note_states:
        if find_note(keep, file_note_state['title']):
            continue

        new_notes_count += 1
        create_note(keep, file_note_state['title'], file_note_state['text'])

    print(f"Uploading {new_notes_count} new notes")
    print('syncing...')
    # This doesn't use sync_up(keep) because we want to fail if there is network issue
    keep.sync()


def check_connection(host='http://google.com'):
    try:
        requests.get(host, timeout=1)
        print("Internet connection present")
        return True
    except requests.exceptions.ConnectionError:
        print("No internet connection")
        return False


@benchmark
def run(keep, note_path):
    note_data = file_to_note_tuple(note_path)
    note = find_note(keep, note_data['title'])

    if note is None:
        note = create_note(keep, note_data['title'], note_data['text'])

        print('syncing...')
        sync_up(keep)
    elif not hash_equal(note.text, note_data['text']):
        note.text = note_data['text']

        print('syncing...')
        sync_up(keep)
    else:
        print('No changes found.')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        # The first argument is always the name of the executable file
        raise Exception('The sync needs exactly one argument - a file path!')

    note_path = sys.argv[1]
    run(note_path)
