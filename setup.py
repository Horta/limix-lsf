import os
import sys

from setuptools import find_packages, setup

PY2 = sys.version_info[0] == 2

def setup_package():
    src_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    old_path = os.getcwd()
    os.chdir(src_path)
    sys.path.insert(0, src_path)

    needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
    pytest_runner = ['pytest-runner'] if needs_pytest else []

    setup_requires = [] + pytest_runner
    install_requires = [
        'pytest', 'scipy>=0.17', 'numpy>=1.9', 'tabulate', 'humanfriendly',
        'tqdm', 'pickle_mixin', 'pickle_blosc'
    ]
    if PY2:
        install_requires += ['futures']
    tests_require = ['pytest']

    metadata = dict(
        name='limix_lsf',
        version='1.0.6.dev2',
        maintainer="Danilo Horta",
        maintainer_email="horta@ebi.ac.uk",
        license="MIT",
        url='http://github.com/Horta/limix-lsf',
        packages=find_packages(),
        install_requires=install_requires,
        setup_requires=setup_requires,
        tests_require=tests_require,
        include_package_data=True,
        zip_safe=True,
        entry_points={'console_scripts': ['bj = limix_lsf.bj:entry_point']},
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ], )

    try:
        setup(**metadata)
    finally:
        del sys.path[0]
        os.chdir(old_path)


if __name__ == '__main__':
    setup_package()
