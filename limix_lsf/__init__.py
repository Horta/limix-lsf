from __future__ import absolute_import as _absolute_import

from pkg_resources import DistributionNotFound as _DistributionNotFound
from pkg_resources import get_distribution as _get_distribution

from . import clusterrun
from .util import kill_group

try:
    __version__ = _get_distribution('limix_lsf').version
except (_DistributionNotFound, AttributeError):
    __version__ = 'unknown'


def test():
    import os
    p = __import__('limix_lsf').__path__[0]
    src_path = os.path.abspath(p)
    old_path = os.getcwd()
    os.chdir(src_path)

    try:
        return_code = __import__('pytest').main(['-q'])
    finally:
        os.chdir(old_path)

    if return_code == 0:
        print("Congratulations. All tests have passed!")

    return return_code


__all__ = ['__version__', 'test', 'clusterrun', 'kill_group']
