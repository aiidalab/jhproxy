#!/usr/bin/env python
from __future__ import absolute_import
from setuptools import setup, find_packages
import os

def get_version():
    """Dumb version parser"""
    initfname = os.path.join(
        os.path.split(os.path.realpath(__file__))[0],
        'jhproxy',
        '__init__.py')
    version = None
    with open(initfname) as f:
        for l in f:
            if '__version__' in l:
                version = l.partition('#')[0].split('=')[1].strip().replace('"', '').replace("'", '')
                break

    if version is None:
        raise RuntimeError("Unable to get package version number")

    if '.' not in version:
        raise RuntimeError("No dots find in version")

    return version


if __name__ == '__main__':
    setup(
        name="jhproxy",
        author="Giovanni Pizzi",
        packages=find_packages(),
        description=
        'A proxy for ports inside Jupyter when running with a DockerSpawner',
        url="https://github.com/aiidalab/jhproxy",
        license="MIT",
        classifiers=["Programming Language :: Python"],
        version=get_version(),
        install_requires=['jupyterhub', 'dockerspawner', 'traitlets'],
    )
