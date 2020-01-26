import gkeepapi
from pathlib import Path
from os import path
import hashlib
import sys
import keyring
import time
import json
from utils import benchmark, traverse_files
import requests

CONFIG = json.load(open('.config.json'))
NOTES_ROOT = path.expanduser(CONFIG['notes_root'])
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
    gnotes = list(
        keep.find(labels=[label], func=lambda note: note.title == title)
    )

    if len(gnotes) > 1:
        raise Exception(f'Too many notes match the title: {title}')
    return (gnotes[0] if len(gnotes) == 1 else None)


def file_to_note_tuple(path):
    relative_path = path.replace(NOTES_ROOT, '')[1:]
    title = relative_path.replace(f".{FILE_EXTENSION}", '')
    print(f"title {title}")

    text = open(path, 'r').read()

    return {'path': path, 'title': title, 'text': text}


def hash_equal(text_a, text_b):
    hash_a = hashlib.md5(text_a.encode('utf-8')).hexdigest()
    hash_b = hashlib.md5(text_b.encode('utf-8')).hexdigest()

    return hash_a == hash_b


@benchmark
def login(keep):
    # keep.login(CONFIG['email'], CONFIG['password'])
    # master_token = keep.getMasterToken()
    # keyring.set_password('google-keep-password', USERNAME, master_token)
    if len(open('.state.json', 'r').read()) == 0:
        # login
        token = keyring.get_password('google-keep-token',
                                     CONFIG['os_username'])
        keep.resume(CONFIG['email'], token)

        # save state
        state_file = open('.state.json', 'w')
        state = keep.dump()
        json.dump(state, state_file)
    else:
        state_file = open('.state.json', 'r')
        state = json.load(state_file)
        token = keyring.get_password('google-keep-token',
                                     CONFIG['os_username'])
        keep.resume(CONFIG['email'], token, state=state)


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
        path = f"{NOTES_ROOT}/{note.title}.{FILE_EXTENSION}"
        print(f'File path: {path}')
        local_content = open(path, 'r').read()
        if not hash_equal(local_content, note.text):
            open(path, 'w').write(note.text)


@benchmark
def upload_new_notes(keep):
    all_paths = traverse_files(NOTES_ROOT)
    file_note_states = list(
        map(
            file_to_note_tuple,
            filter(lambda path: path[-3:] == f".{FILE_EXTENSION}", all_paths)
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
