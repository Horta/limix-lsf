
import re
from io import StringIO
import humanfriendly as hf
from limix_util.pickle import SlotPickleMixin
from . import util


class Job(SlotPickleMixin):
    __slots__ = ['jobid', 'finished', '_exit_status', 'cmd', '_bcmd',
                 'odata', 'edata', 'runid', '_hasfinished', '_stat_cache',
                 'mkl_nthreads']

    def __init__(self, jobid, cmd):
        self.runid = None
        self.jobid = jobid
        self._exit_status = None
        self._hasfinished = False
        self.cmd = cmd
        self._bcmd = []
        self.odata = ''
        self.edata = ''
        self.mkl_nthreads = 1
        self._stat_cache = None

    def stdout(self):
        (fp, _) = util.get_output_files(self.jobid, self.runid)
        try:
            with open(fp, 'r') as f:
                return f.read()
        except IOError:
            return None
        return None

    def stderr(self):
        (_, fp) = util.get_output_files(self.jobid, self.runid)
        try:
            with open(fp, 'r') as f:
                return f.read()
        except IOError:
            return None
        return None

    @property
    def group(self):
        return '/cluster/%s' % self.runid

    @property
    def submission_status(self):
        if self.os_jobid:
            return 'success'
        return self.edata

    @property
    def os_jobid(self):
        m = re.match(r'^Job <(\d+)>.*$', self.odata)
        if m:
            return int(m.group(1))
        return None

    @property
    def bcmd(self):
        return self._bcmd

    @bcmd.setter
    def bcmd(self, bc):
        self._bcmd = bc

    @property
    def full_cmd(self):
        n = self.mkl_nthreads
        middle  = ['env', 'MKL_NUM_THREADS=%d' % n]
        middle += ['MKL_DYNAMIC=TRUE']
        return self.bcmd + middle + self.cmd

    def stat(self):
        if self._stat_cache:
            return self._stat_cache

        stats = util.get_jobs_stat()

        if self.os_jobid not in stats:
            if self.hassubmitted():
                self._stat_cache = 'DONE_OR_EXIT'
                return self._stat_cache
            else:
                return 'UNKNOWN'

        r = stats[self.os_jobid]
        if r == 'DONE' or r == 'EXIT':
            self._stat_cache = r
        return r

    def hassubmitted(self):
        return ("Job <%d> " % self.os_jobid + "is submitted") in self.odata

    def ispending(self):
        return self.stat() == 'PEND'

    def isrunning(self):
        return self.stat() == 'RUN'

    def hasfinished(self):
        if self._hasfinished:
            return True
        self._hasfinished = (self.stat() == 'DONE' or self.stat() == 'EXIT' or
                             self.stat() == 'DONE_OR_EXIT')
        return self._hasfinished

    def exit_status(self):
        if not self.hasfinished():
            return None

        if self._exit_status is not None:
            return self._exit_status

        data = self.stdout()
        if data is None:
            return None

        buf = StringIO(data)
        found = False
        for line in buf:
            if line.strip() == 'Your job looked like:':
                found = True
                break

        if found:
            buf.readline()
            buf.readline()
            buf.readline()
            buf.readline()
            buf.readline()
            buf.readline()
            status_msg = buf.readline().strip()
            if status_msg == 'Successfully completed.':
                self._exit_status = 0
            else:
                m = re.match(r'^Exited with exit code (\d+)\.$', status_msg)
                if m is None:
                    self._exit_status = -1
                else:
                    self._exit_status = int(m.group(1))
        else:
            self._exit_status = None

        return self._exit_status

    def resource_info(self):
        if not self.hasfinished():
            return None
        data = self.stdout()

        if data is None:
            return None

        buf = StringIO(data)
        found = False
        for line in buf:
            if line.strip() == 'Resource usage summary:':
                found = True
                break

        if found:
            buf.readline()
            cpu_time = buf.readline()
            max_memory = buf.readline()
            m = re.match(r'^.*Max Memory : [^\d]*(\d.*)$', max_memory)
            if m is None:
                max_memory = None
            else:
                max_memory = hf.parse_size(m.group(1))
            avg_memory = buf.readline()
            req_memory = buf.readline()
            m = re.match(r'^.*Total Requested Memory : [^\d]*(\d.*)$', req_memory)
            if m is None:
                req_memory = None
            else:
                req_memory = hf.parse_size(m.group(1))
            delta_memory = buf.readline()
            return dict(max_memory=max_memory, req_memory=req_memory)

        return None

    #
    # def stdout(self):
    #     ofile, _ = _get_output_files(self.jobid, self.runid)
    #     try:
    #         with open(ofile, 'r') as f:
    #             return f.read()
    #     except IOError:
    #         return ""
    #
    # def stderr(self):
    #     _, efile = _get_output_files(self.jobid, self.runid)
    #     try:
    #         with open(efile, 'r') as f:
    #             return f.read()
