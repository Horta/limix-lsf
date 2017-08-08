import re
# from io import StringIO
from os.path import exists

from ._string import make_sure_unicode
from .util import get_jobs_stat


# from humanfriendly import parse_size


class BJob(object):
    def __init__(self, bjob_id=None, fp_out=None, fp_err=None):
        self._bjob_id = None
        self._stat = None
        self._exit_status = None
        self._hasfinished = False
        self._exit_status = None

        if bjob_id is None:
            self._init_from_output(fp_out, fp_err)

    def _init_from_output(self, fp_out, fp_err):
        if exists(fp_out):
            self._process_stdout(fp_out)

        if exists(fp_err):
            self._process_stderr(fp_err)

        self._process_stat()

    def _process_stdout(self, fp_out):
        with open(fp_out, 'r') as f:
            out = f.read()
            self._bjob_id = _bjob_id(out)

    @property
    def stat(self):
        return self._stat

    def _process_stat(self):
        stats = util.get_jobs_stat()

        if self._bjob_id in stats:
            self._stat = stats[self._bjob_id]

        else:
            self._stat = 'UNKNOWN'

    def ispending(self):
        return self.stat == 'PEND'

    def isrunning(self):
        return self.stat == 'RUN'

    def hasfinished(self):
        if self._hasfinished:
            return True

        self._hasfinished = (self.stat() == 'DONE' or self.stat() == 'EXIT'
                             or self.stat() == 'DONE_OR_EXIT')

        return self._hasfinished


def _bjob_id(out):
    m = re.match(r'^Subject: Job (\d+):.*$', make_sure_unicode(out))
    if m:
        return int(m.group(1))
    return None
