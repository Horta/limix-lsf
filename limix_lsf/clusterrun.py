
from concurrent.futures import ProcessPoolExecutor
import logging
import os
from os.path import join
from copy import copy
import re
import atexit
import subprocess
from subprocess import list2cmdline
import humanfriendly as hf
from limix_util.report import BeginEnd, ProgressBar
import limix_util.pickle as pickle_
from limix_util.path import make_sure_path_exists
from limix_util.path import touch
from . import config
from . import util
from . import job

_cluster_runs = dict()
def load(runid):
    if runid not in _cluster_runs:
        folder = join(config.stdoe_folder(), runid)
        if os.path.exists(join(folder, '.deleted')):
            return None
        cr = pickle_.unpickle(join(folder, 'cluster_run.pkl'))
        _cluster_runs[runid] = cr
    return _cluster_runs[runid]

def rm(runid):
    folder = join(config.stdoe_folder(), runid)
    touch(join(folder, '.deleted'))

def exists(runid):
    if runid not in _cluster_runs:
        return os.path.exists(join(config.stdoe_folder(), runid,
                                   'cluster_run.pkl'))
    return True

def _submit_job(job):
    fcmd = job.full_cmd
    p = subprocess.Popen(list2cmdline(fcmd), shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (job.odata, job.edata) = p.communicate()
    p.stdout.close()
    p.stderr.close()
    return job

class ClusterRunBase(pickle_.SlotPickleMixin):
    __slots__ = ['requests', 'megabytes', 'jobs', 'group', 'runid', 'title',
                 'nprocs', 'mkl_nthreads', 'queue']
    def __init__(self, title):
        self.requests = []
        self.megabytes = 4096
        self.nprocs = 1
        self.jobs = []
        self.runid = None
        self.title = title
        self.mkl_nthreads = 1
        self.queue = None

class ClusterRun(ClusterRunBase):
    __slots__ = []
    def __init__(self, title='notitle'):
        super(ClusterRun, self).__init__(title)

    def store(self):
        with BeginEnd('Storing cluster commands', silent=True):
            pickle_.pickle(self, join(config.stdoe_folder(), self.runid,
                           'cluster_run.pkl'))

    def request(self, req):
        if self.runid is not None:
            raise Exception('This command set has already been sent.')

        if req == 'panfs':
            self.requests.append('panfs_nobackup_production')
        elif req == 'fasttmp':
            self.requests.append('fasttmp')
        elif req == 'gpfs':
            self.requests.append('gpfs')
        else:
            raise Exception("Don't know about %s." % req)

    def kill(self, block=True):
        grp = '/cluster/%s' % self.runid
        util.kill_group(grp, block=block)


    @property
    def memory(self):
        nbytes = int(round(self.megabytes / 1024. / 1024.))
        return hf.format_size(nbytes)

    @memory.setter
    def memory(self, siz):
        if self.runid is not None:
            raise Exception('This command set has already been sent.')

        nbytes = hf.parse_size(siz)
        self.megabytes = int(round(nbytes / 1024. / 1024.))

    def add(self, cmd):
        if self.runid is not None:
            raise Exception('This command set has already been sent.')

        cmd = cmd if isinstance(cmd, list) else [cmd]
        cmd = [str(c) for c in cmd]

        j = job.Job(len(self.jobs), cmd)
        self.jobs.append(j)

    def _dryrun_job(self, job):
        print(list2cmdline(job.full_cmd))

    # def _parallel_run_job(self, executor, job):
    #     fcmd = job.full_cmd
    #     f = executor.submit(subprocess.Popen, list2cmdline(fcmd), shell=True,
    #                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     # process = subprocess.Popen(list2cmdline(fcmd), shell=True,
    #     #                  stdout=subprocess.PIPE,
    #     #                  stderr=subprocess.PIPE)
    #     return f

    # def _run_job_wait(self, executor, job):
    #     fcmd = job.full_cmd
    #     f = executor.submit(subprocess.Popen, list2cmdline(fcmd), shell=True,
    #                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _sequential_run_job(self, job):
        os.system(list2cmdline(job.cmd))

    def resubmit(self, jobid):
        raise NotImplementedError('me implementa ai porra')

    def run(self, dryrun=False):
        if self.runid is not None:
            raise Exception('This command set has already been sent.')

        self.runid = _generate_runid()
        if not dryrun:
            make_sure_path_exists(join(config.stdoe_folder(), self.runid))
        bcmd = self._init_parse()
        self._parse_requests(bcmd)
        self._parse_memory(bcmd)
        self._parse_nprocs(bcmd)
        bcmd += ['-g', '/cluster/%s' % self.runid]
        if self.queue:
            bcmd += ['-q', self.queue]
        self._end_parse(bcmd)

        ujobs = []
        max_workers = 500
        with BeginEnd('Submitting jobs'):
            pb = ProgressBar(len(self.jobs))
            i = 0
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                for job in executor.map(_submit_job, self.jobs):
                    job.runid = self.runid
                    ujobs.append(job)
                    i += 1
                    pb.update(i)
            pb.finish()

        self.jobs = ujobs
        print('   %d jobs have been submitted   '
              % len(self.jobs))

        print("Run ID: %s" % self.runid)

        self.store()

        return self.runid

    def _init_parse(self):
        return ['bsub']

    def _end_parse(self, bcmd):
        for job in self.jobs:
            ofile, efile = self._get_output_files(job.jobid)
            job.bcmd = copy(bcmd) + ['-o', ofile, '-e', efile]
            job.mkl_nthreads = self.mkl_nthreads

    def _get_output_files(self, jobid):
        _max_nfiles = 1000
        pr = str(int(jobid / _max_nfiles))
        base = join(config.stdoe_folder(), self.runid, pr)
        make_sure_path_exists(base)
        ofile = join(base, 'out_%d.txt' % jobid)
        efile = join(base, 'err_%d.txt' % jobid)
        return (ofile, efile)


    def _parse_requests(self, bcmd):
        bcmd.append("-R")
        bcmd.append("select[%s]" % (','.join(self.requests)))

    def _parse_memory(self, bcmd):
        m = self.megabytes
        bcmd.append("-M")
        bcmd.append("%d" % m)
        bcmd.append("-R")
        bcmd.append("rusage[mem=%d]" % m)

    def _parse_nprocs(self, bcmd):
        bcmd.append('-n')
        bcmd.append('%d' % self.nprocs)

    def __str__(self):
        njobs = len(self.jobs)
        if njobs == 0:
            return self.runid + ': no job'
        jsum = list2cmdline(self.jobs[0].cmd)
        return self.runid + ' (%d jobs): %s' % (njobs, jsum)

    @property
    def number_jobs(self):
        return len(self.jobs)

    @property
    def number_jobs_pending(self):
        return sum([1 for job in self.jobs if job.ispending()])

    @property
    def number_jobs_running(self):
        return sum([1 for job in self.jobs if job.isrunning()])

    @property
    def number_jobs_finished(self):
        return sum([1 for job in self.jobs if job.hasfinished()])

    @property
    def number_jobs_succeed(self):
        return sum([1 for job in self.jobs if job.hasfinished() and\
                                              job.exit_status() == 0])

    @property
    def number_jobs_failed(self):
        return sum([1 for job in self.jobs if job.hasfinished() and\
                                              job.exit_status() != 0])

def _generate_runid():
    from time import gmtime, strftime
    return strftime('%Y-%m-%d-%H-%M-%S', gmtime())

_registered_cluster_runs = dict()
def _register_cluster_run(cr):
    if id(cr) not in _registered_cluster_runs:
        _registered_cluster_runs[id(cr)] = cr

def _update_storage():
    for cr in list(_registered_cluster_runs.values()):
        cr.store()
atexit.register(_update_storage)

def get_bjob(runid, jobid):
    cr = load(runid)
    _register_cluster_run(cr)
    return cr.jobs[jobid]

def get_groups_summary(nlast=10):

    awk = "awk -F\" \" '{print $1, $2, $3, $4, $5, $6, $7}'"
    cmd = "bjgroup | grep -E \".*`whoami`$\" | %s" % awk
    msg = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    msg = msg.strip()
    lines = msg.split('\n')
    table = [line.split(' ') for line in lines]

    table = _clear_groups_summary(table)
    table.sort(key=lambda x: x[0], reverse=True)

    table_out = []
    logger = logging.getLogger(__file__)
    for row in table:
        runid = row[0].strip('/').split('/')[1]
        try:
            cr = load(runid)
            if cr is None:
                continue
        except ImportError as e:
            logger.warn('Could not load cluster run %s. Reason: %s.', runid,
                        str(e))
            row.append('UNK')
            row.append('UNK')
            row.append('UNK')
        except IOError as e:
            pass
        #     logger.warn('Could not load cluster run %s. Reason: %s.', runid,
        #                 str(e))
        #     row.append('UNK')
        #     row.append('UNK')
        #     row.append('UNK')
        else:
            try:
                row.append(cr.number_jobs_failed)
            except TypeError:
                row.append('UNK')

            try:
                row.append(cr.number_jobs_succeed)
            except TypeError:
                row.append('UNK')

            try:
                row.append(cr.title)
            except TypeError:
                row.append('UNK')

            table_out.insert(0, row)
            if len(table_out) >= nlast:
                break

    header = ['group_name', 'njobs', 'pend', 'run', 'ssusp', 'ususp', 'finish',
              'failed', 'succeed', 'title']
    table_out.insert(0, header)
    return table_out

def _clear_groups_summary(table):
    ntable = []
    for row in table:
        if not _isrun_group(row[0]):
            continue
        row[1:] = [int(c) for c in row[1:]]
        ntable.append(row)
    return ntable

def _isrun_group(name):
    name = name.strip('/')
    names = name.split('/')
    if len(names) != 2:
        return False
    return names[0] == 'cluster' and _isrunid(names[1])

_runid_matcher = re.compile(r'^\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d$')
def _isrunid(runid):
    return _runid_matcher.match(runid) is not None
