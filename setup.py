from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from glob import glob

setup(
    name = "beast_whip",
    version = "0.0.9",
    packages = find_packages(),
    scripts = glob('bin/*'),
    install_requires = [
        'lxml',
        'argparse', # For python 2.6 compatibility
        'mock',
        'nose'
    ]
)
