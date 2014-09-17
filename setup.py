from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from glob import glob

setup(
    name = "beagle-optimiser",
    version = "0.0.9",
    packages = find_packages(),
    scripts = glob('bin/*'),
    install_requires = [
        'argparse',
        'mock',
        'nose'
    ]
)