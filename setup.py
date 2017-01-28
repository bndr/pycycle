#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import sys
from os.path import dirname

from setuptools import setup

here = os.path.abspath(dirname(__file__))

with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

base_dir = os.path.dirname(__file__)

about = {}
with open(os.path.join(base_dir, "pycycle", "__version__.py")) as f:
    exec(f.read(), about)

required = [
    'crayons',
    'click>=6.7',
    'click-completion',
    'pytest'
]

setup(
    name='pycycle',
    version=about['__version__'],
    description='Find and repair your import cycles in any project',
    long_description=long_description,
    author='Vadim Kravcenko',
    author_email='vadim.kravcenko@gmail.com',
    url='https://github.com/bndr/pycycle',
    packages=['pycycle'],
    entry_points={
        'console_scripts': ['pycycle=pycycle:cli'],
    },
    install_requires=required,
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    license='MIT',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)