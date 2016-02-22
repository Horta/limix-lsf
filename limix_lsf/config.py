import json
import os

def root_dir():
    return json.load(open(os.path.join(os.path.expanduser('~'),
                         'cluster_properties.json'), 'r'))['base_dir']

def cluster_oe_folder():
    return json.load(open(os.path.join(os.path.expanduser('~'),
                         'cluster_properties.json'), 'r'))['cluster_oe']
