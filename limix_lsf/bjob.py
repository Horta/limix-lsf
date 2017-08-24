import re
import subprocess
from os import remove
from os.path import exists

from ._string import make_sure_unicode
from .util import get_jobs_stat, touch


# from humanfriendly import parse_size


class BJob(object):
    def __init__(self, bjob_id=None, fp_out=None, fp_err=None):
        self._bjob_id = None
        self._stat = None
        self._exit_status = None
        self._hasfinished = False
        self._fp_out = None
        self._fp_err = None

        if bjob_id is None:
            self._fp_out = fp_out
            self._fp_err = fp_err
            self._init_from_output()

    def _init_from_output(self):
        if exists(self._fp_out):
            self._process_stdout()

        if exists(self._fp_err):
            self._process_stderr()

        self._process_stat()

    def _process_stdout(self):
        with open(self._fp_out, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                self._bjob_id = _bjob_id(lines[1])
            self._process_exit_status(lines)

    def _process_stderr(self):
        pass
        # with open(fp_out, 'r') as f:
        #     lines = f.readlines()
        #     self._bjob_id = _bjob_id(lines[1])

    def kill(self):
        if self._bjob_id is not None:
            subprocess.call("bkill %d" % self._bjob_id, shell=True)

    @property
    def stdout(self):
        if not exists(self._fp_out):
            return None

        with open(self._fp_out, 'r') as f:
            return f.read()

    @property
    def stderr(self):
        if not exists(self._fp_err):
            return None

        with open(self._fp_err, 'r') as f:
            return f.read()

    def remove_output(self):
        if exists(self._fp_err):
            remove(self._fp_err)

        if exists(self._fp_out):
            remove(self._fp_out)

    def touch_output(self):
        touch(self._fp_err)
        touch(self._fp_out)

    @property
    def memory_usage(self):
        mem = {"Max Memory": None, "Average Memory": None,
               "Total Requested Memory": None, "Delta Memory": None}

        count = len(mem)
        if exists(self._fp_out):
            with open(self._fp_out, 'r') as f:
                lines = f.readlines()
            for line in lines:
                l = line.strip()
                for k in mem.keys():
                    if l.startswith(k):
                        mem[k] = re.match(".*:(.*)", l).group(1).strip()
                        count -= 1
                        break
                if count == 0:
                    break
        return mem

    @property
    def stat(self):
        return self._stat

    def _process_stat(self):
        stats = get_jobs_stat()

        if self._bjob_id in stats:
            self._stat = stats[self._bjob_id]

        else:
            self._stat = 'UNKNOWN'

    @property
    def hasoutput(self):
        has = False
        if self._fp_out is not None:
            has |= exists(self._fp_out)

        if self._fp_err is not None:
            has |= exists(self._fp_err)

        return has

    @property
    def submitted(self):
        return (self.hasoutput or self.ispending or self.isrunning
                or self.hasfinished)

    @property
    def ispending(self):
        return self.stat == 'PEND'

    @property
    def isrunning(self):
        return self.stat == 'RUN'

    @property
    def hasfinished(self):
        if self._hasfinished:
            return True

        self._hasfinished = (self.stat == 'DONE' or self.stat == 'EXIT'
                             or self.stat == 'DONE_OR_EXIT')

        if not self._hasfinished:
            self._hasfinished = self._exit_status is not None

        return self._hasfinished
    
    @property
    def fail_reason(self):
        if exists(self._fp_out):
            with open(self._fp_out, 'r') as f:
                lines = f.readlines()
            for line in lines:
                if line.strip() == "TERM_MEMLIMIT: job killed after reaching LSF memory usage limit.":
                    return "MEMLIMIT"
        return "UNK"

    @property
    def exit_status(self):
        return self._exit_status

    def _process_exit_status(self, lines):
        found = False
        for i in range(len(lines)):
            if lines[i].strip() == 'Your job looked like:':
                found = True
                j = i + 7
                break

        if found and j < len(lines):
            status_msg = lines[j].strip()

            if status_msg == 'Successfully completed.':
                self._exit_status = 0
            else:
                self._exit_status = _get_err_exit_code(status_msg)


def _get_err_exit_code(status_msg):

    m = re.match(r'^Exited with exit code (\d+)\.$', status_msg)

    if m is None:
        return -1

    return int(m.group(1))


def _bjob_id(out):
    m = re.match(r'^Subject: Job (\d+):.*$', make_sure_unicode(out))
    if m:
        return int(m.group(1))
    return None
