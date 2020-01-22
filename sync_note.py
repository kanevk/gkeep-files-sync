import gkeepapi
from pathlib import Path
import hashlib
import sys
import keyring
import time
import json
import utils
import requests

HOME = str(Path.home())
CONFIG = json.load(open('.config.json'))


def benchmark(func):
    """
    A benchmark tool
    """
    def function_timer(*args, **kwargs):
        start = time.time()
        value = func(*args, **kwargs)
        end = time.time()
        runtime = end - start
        print(
            f"`{func.__name__}` took {runtime} seconds"
        )
        return value
    return function_timer


def create_note(keep, title, text):
    print(f"Creating a note {title}")
    newNote = keep.createNote(title, text)
    label = keep.findLabel('autosync')
    newNote.labels.add(label)
    #
    return newNote


def find_note(keep, title):
    label = keep.findLabel('autosync')
    gnotes = list(
        keep.find(labels=[label], func=lambda note: note.title == title)
    )
    #
    if len(gnotes) > 1:
        raise Exception(f'Too many notes match the title: {title}')
    return (gnotes[0] if len(gnotes) == 1 else None)


def file_to_note_tuple(path):
    path_after_home = path.replace(HOME, '')
    title = path_after_home[1:].replace('/', ' ').replace('.md', '')
    text = open(path, 'r').read()
    #
    return {'path': path, 'title': title, 'text': text}


def hash_equal(text_a, text_b):
    hash_a = hashlib.md5(text_a.encode('utf-8')).hexdigest()
    hash_b = hashlib.md5(text_b.encode('utf-8')).hexdigest()
    #
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
        #
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

    remote_notes = list(keep.find(labels=[keep.findLabel('autosync')]))

    for note in remote_notes:
        path = f"{HOME}/{note.title.replace(' ', '/')}.md"
        local_content = open(path, 'r').read()
        if not hash_equal(local_content, note.text):
            open(path, 'w').write(note.text)


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
        #
        print('syncing...')
        sync_up(keep)
    elif not hash_equal(note.text, note_data['text']):
        note.text = note_data['text']
        #
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
