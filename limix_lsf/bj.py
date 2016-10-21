
from argparse import ArgumentParser
from tabulate import tabulate
import logging
from . import clusterrun
from . import util
from . import config

def do_root(_):
    print(config.stdoe_folder())

def _do_run_status(runid):
    cc = clusterrun.load(runid)
    if cc is None:
        print('Runid %s could not be found.' % runid)
        return

    print(cc.number_jobs)
    print(cc.number_jobs_pending)
    print(cc.number_jobs_running)
    print(cc.number_jobs_finished)
    print('exit status', cc.jobs[0].exit_status())
    # cc.get_number_jobs_failed()

def _do_global_status(nlast):
    table = clusterrun.get_groups_summary(nlast)
    print(tabulate(table))

def do_status(args):
    if args.runid:
        runid = util.proper_runid(args.runid)
        _do_run_status(runid)
    else:
        _do_global_status(args.nlast)

def do_killall(_):
    util.killall(force=True)

# def do_remove_group(args):
#
#     # grps = cluster.get_group_names()
#     if args.what == 'alien':
#         cluster.remove_alien_groups()
#         # rexp = r'/cluster/\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d'
#         # c = re.compile(rexp)
#         # conforming = [g for g in grps if c.match(g)]
#
#
# def _do_remove_run(runids):
#     paths = [join(cluster.base_folder, r) for r in runids]
#     lu.path_.rrm(paths)
#
# def do_remove_run(args):
#     import dateparser
#
#     if args.older_than is None:
#         return
#
#     runids = cluster.get_runids()
#
#     old_runids = []
#     for runid in runids:
#         if dateparser.parse(runid) < dateparser.parse(args.older_than):
#             old_runids.append(runid)
#
#     with lu.BeginEnd('Removing %d folders' % len(old_runids)):
#         _do_remove_run(old_runids)

def entry_point():
    logging.basicConfig()
    p = ArgumentParser()
    sub = p.add_subparsers()

    s = sub.add_parser('root')
    s.set_defaults(func=do_root)

    # s = sub.add_parser('hist')
    # s.add_argument('--last_n', type=int, default=5)
    # s.set_defaults(func=do_hist)

    s = sub.add_parser('status')
    s.add_argument('runid', nargs='?', default=None)
    s.add_argument('--nlast', default=10, type=int)
    s.set_defaults(func=do_status)

    s = sub.add_parser('killall')
    s.set_defaults(func=do_killall)

    #
    # s = sub.add_parser('rm-run')
    # s.add_argument('--older_than', default=None)
    # s.set_defaults(func=do_remove_run)
    #
    # s = sub.add_parser('rm-group')
    # s.add_argument('what', choices=['alien'])
    # s.set_defaults(func=do_remove_group)
    #
    # # s = sub.add_parser('root')
    # # s.set_defaults(func=do_root)

    args = p.parse_args()
    func = args.func
    del args.func
    func(args)
