from __future__ import unicode_literals

import os

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def stdoe_folder():
    home = os.path.join(os.path.expanduser('~'))
    conf = configparser.ConfigParser()
    conf.read(os.path.join(home, '.config', 'lsf', 'config'))
    return conf.get('default', 'stdoe_folder')
