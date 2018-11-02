#!/usr/bin/env python

from __future__ import absolute_import
from setuptools import setup, find_packages

if __name__ == '__main__':
    # Provide static information in setup.json
    # such that it can be discovered automatically
    setup(
        name="jhproxy",
        author="Giovanni Pizzi",
        packages=find_packages(),
        description=
        'A proxy for ports inside Jupyter when running with a DockerSpawner',
        #url=
        license="MIT",
        classifiers=["Programming Language :: Python"],
        version="0.0.1",
        install_requires=['jupyterhub', 'dockerspawner'],
    )
