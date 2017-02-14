import errno
from os import makedirs, utime


def make_sure_path_exists(path):
    """Creates a path recursively if necessary.
    """
    try:
        makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


def touch(fname, times=None):
    """Creates an empty file."""
    with open(fname, 'a'):
        utime(fname, times)
