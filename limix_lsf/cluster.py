# import subprocess
# from subprocess import Popen
# import os
# import humanfriendly as hf
# from os.path import join
# import limix_util as lu
# from subprocess import list2cmdline
# from copy import copy
# import cStringIO as StringIO
# import re
# import atexit
# from config import cluster_oe_folder
#
# _max_nfiles = 1000
#
# _registered_cluster_runs = dict()
# def _register_cluster_run(cr):
#     if id(cr) not in _registered_cluster_runs:
#         _registered_cluster_runs[id(cr)] = cr
#
# def update_storage():
#     for cr in _registered_cluster_runs.values():
#         cr.store()
# atexit.register(update_storage)
#
# def get_bjob(runid, jobid, verbose=True):
#     cr = load_cluster_run(runid, verbose=verbose)
#     _register_cluster_run(cr)
#     return cr.jobs[jobid]
#
# def get_conforming_groups():
#     grps = get_group_names()
#     rexp = r'^/cluster(/\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d)?$'
#     c = re.compile(rexp)
#     return [g for g in grps if c.match(g)]
#
# def remove_alien_groups():
#     grps = get_group_names()
#     conforming = get_conforming_groups()
#     grps = set(grps).difference(conforming)
#     if len(grps) == 0:
#         print('There is no alien group to be removed.')
#         return
#
#     cmds = ['bgdel ' + g for g in grps]
#     yes = lu.misc.query_yes_no(('There are %d alien groups.' % len(cmds)) +
#                          ' Are you sure you want to remove all of them?',
#                          default='no')
#     if yes:
#         for cmd in cmds:
#             subprocess.Popen(cmd, shell=True)
#
# def humanfriendly_runid(runid):
#     return "%s-%s-%s %s:%s:%s" % runid.split('-')
#
# _cluster_runs = dict()
# def load_cluster_run(runid, verbose=True):
#     if runid not in _cluster_runs:
#         with lu.BeginEnd('Loading cluster commands', not verbose):
#             cr = lu.pickle_.unpickle(join(cluster_oe_folder(), runid, 'cluster_run.pkl'))
#             _cluster_runs[runid] = cr
#     return _cluster_runs[runid]
#
# def create_run():
#     lu.path_.make_sure_path_exists(cluster_oe_folder())
#     return ClusterRun()
#
# def get_runids():
#     c = re.compile(r'^\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d$')
#     files = os.listdir(cluster_oe_folder())
#     runids = [f for f in files if c.match(f)]
#     return runids
#
# _runid_matcher = re.compile(r'^\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d$')
# def _isrunid(runid):
#     return _runid_matcher.match(runid) is not None
#
# def _isrun_group(name):
#     name = name.strip('/')
#     names = name.split('/')
#     if len(names) != 2:
#         return False
#     return names[0] == 'cluster' and _isrunid(names[1])
#
# def get_active_runs():
#     # get_conforming_groups
#     msg = subprocess.check_output('bjobs -g /cluster -u `whoami`',
#                                   shell=True, stderr=subprocess.STDOUT)
#     msg = msg.strip()
#     if msg == 'No unfinished job found':
#         return []
#
# def get_group_names():
#     cmd = "bjgroup | grep -E \".*`whoami`$\" | awk -F\" \" '{print $1}'"
#     msg = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
#     msg = msg.strip()
#     return list(set(msg.split('\n')))
#
# def get_groups_summary():
#     nlast = 10
#
#     awk = "awk -F\" \" '{print $1, $2, $3, $4, $5, $6, $7}'"
#     cmd = "bjgroup | grep -E \".*`whoami`$\" | %s" % awk
#     msg = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
#     msg = msg.strip()
#     lines = msg.split('\n')
#     table = [line.split(' ') for line in lines]
#
#     table = _clear_groups_summary(table)
#     table.sort(key=lambda x: x[0])
#     if len(table) > nlast:
#         table = table[-nlast:]
#
#     cruns = []
#     for row in table:
#         runid = row[0].strip('/').split('/')[1]
#         cr = load_cluster_run(runid, verbose=False)
#         cruns.append(cr)
#         row.append(cr.number_jobs_failed)
#         row.append(cr.number_jobs_succeed)
#
#     header = ['group_name', 'njobs', 'pend', 'run', 'ssusp', 'ususp', 'finish',
#               'failed', 'succeed']
#     table.insert(0, header)
#     return table
#
# _stats = [None]
# def _get_jobs_stat():
#     if _stats[0] is None:
#         cmd = 'bjobs -a -o "JOBID STAT" -noheader'
#         r = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
#         r = r.strip()
#         if r == 'No job found':
#             _stats[0] = {}
#         else:
#             try:
#                 _stats[0] = {int(row.split(' ')[0]):row.split(' ')[1] for row in r.split('\n')}
#             except Exception as e:
#                 import ipdb; ipdb.set_trace()
#                 pass
#     return _stats[0]
#
# def _clear_groups_summary(table):
#     ntable = []
#     for row in table:
#         if not _isrun_group(row[0]):
#             continue
#         row[1:] = [int(c) for c in row[1:]]
#         ntable.append(row)
#     return ntable
#
#
#
# def group_jobids(grp):
#     procs = Popen("bjobs -g %s -w | awk '{print $1}'" % grp,
#                   shell=True, stdout=subprocess.PIPE).stdout.read()
#     procs = procs.split('\n')
#     procs = procs[1:-1]
#     return [int(p) for p in procs]
#
# def kill_group(grp, block=True):
#     jobids = group_jobids(grp)
#     procs = []
#     for jobid in jobids:
#         p = Popen("bkill %d &> /dev/null" % jobid, shell=True)
#         procs.append(p)
#
#     if block:
#         for p in procs:
#             p.wait()
#
# def _store_cluster_run(cm, verbose=True):
#     with lu.BeginEnd('Storing cluster commands', silent=not verbose):
#         lu.pickle_.pickle(cm, join(cluster_oe_folder(), cm.runid, 'cluster_run.pkl'))
#
# def _get_output_files(i, runid):
#     pr = str(int(i / _max_nfiles))
#     base = join(cluster_oe_folder(), runid, pr)
#     lu.path_.make_sure_path_exists(base)
#     ofile = join(base, 'out_%d.txt' % i)
#     efile = join(base, 'err_%d.txt' % i)
#     return (ofile, efile)
#
# def _generate_runid():
#     from time import gmtime, strftime
#     return strftime('%Y-%m-%d-%H-%M-%S', gmtime())
#
# def _get_last_runid(n):
#     files = os.listdir(cluster_oe_folder())
#     return sorted(files)[len(files)-n-1]
#
# def proper_runid(what):
#     m = re.match(r'^last(\^*)$', what)
#     if m is None:
#         return what
#     n = len(m.group(1)) + 1
#     runids = get_runids()
#     runids.sort()
#     return runids[max(-len(runids), -n)]
#
# if __name__ == '__main__':
#     cmd = create_run()
#     cmd.request('panfs')
#     cmd.request('fasttmp')
#     cmd.memory = '12G'
#     cmd.add('ls')
#     cmd.add('echo hello')
#     runid = cmd.run(dryrun=True)
#     print runid
