from subprocess import Popen
import os
import subprocess
import clusterrun
import re
import config

def group_jobids(grp):
    procs = Popen("bjobs -g %s -w | awk '{print $1}'" % grp,
                  shell=True, stdout=subprocess.PIPE).stdout.read()
    procs = procs.split('\n')
    procs = procs[1:-1]
    return [int(p) for p in procs]

def kill_group(grp, block=True):
    jobids = group_jobids(grp)
    procs = []
    for jobid in jobids:
        p = Popen("bkill %d &> /dev/null" % jobid, shell=True)
        procs.append(p)

    if block:
        for p in procs:
            p.wait()

def get_groups_summary():
    nlast = 10

    awk = "awk -F\" \" '{print $1, $2, $3, $4, $5, $6, $7}'"
    cmd = "bjgroup | grep -E \".*`whoami`$\" | %s" % awk
    msg = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    msg = msg.strip()
    lines = msg.split('\n')
    table = [line.split(' ') for line in lines]

    table = _clear_groups_summary(table)
    table.sort(key=lambda x: x[0])
    if len(table) > nlast:
        table = table[-nlast:]

    cruns = []
    for row in table:
        runid = row[0].strip('/').split('/')[1]
        cr = clusterrun.load(runid)
        cruns.append(cr)
        row.append(cr.number_jobs_failed)
        row.append(cr.number_jobs_succeed)

    header = ['group_name', 'njobs', 'pend', 'run', 'ssusp', 'ususp', 'finish',
              'failed', 'succeed']
    table.insert(0, header)
    return table

def _try_clean_runid(runid):
    c = re.compile(r'^.*(\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d).*$')
    m = c.match(runid)
    if m is None:
        return runid
    return m.group(1)

def proper_runid(what):
    m = re.match(r'^last(\^*)$', what)
    if m is None:
        return _try_clean_runid(what)
    n = len(m.group(1)) + 1
    runids = get_runids()
    runids.sort()
    return runids[max(-len(runids), -n)]

def get_runids():
    c = re.compile(r'^\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d$')
    files = os.listdir(config.cluster_oe_folder())
    runids = [f for f in files if c.match(f)]
    return runids

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
