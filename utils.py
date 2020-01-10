from os import listdir
from os.path import isfile, join


def traverse_files(path):
    files = []
    for f in listdir(path):
        if isfile(join(path, f)):
            files.append(join(path, f))
        else:
            files += traverse_files(join(path, f))
    #
    return files
