from __future__ import unicode_literals

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

def entry_point():
    logging.basicConfig()
    p = ArgumentParser()
    sub = p.add_subparsers()

    s = sub.add_parser('root')
    s.set_defaults(func=do_root)

    s = sub.add_parser('status')
    s.add_argument('runid', nargs='?', default=None)
    s.add_argument('--nlast', default=10, type=int)
    s.set_defaults(func=do_status)

    s = sub.add_parser('killall')
    s.set_defaults(func=do_killall)

    args = p.parse_args()
    func = args.func
    del args.func
    func(args)
