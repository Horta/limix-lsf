import os
import ConfigParser

def stdoe_folder():
    home = os.path.join(os.path.expanduser('~'))
    conf = ConfigParser.ConfigParser()
    conf.read(os.path.join(home, '.config', 'lsf', 'config'))
    return conf.get('DEFAULT', 'stdoe_folder')
