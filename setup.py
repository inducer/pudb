#!/usr/bin/env python
from __future__ import with_statement

from distribute_setup import use_setuptools

use_setuptools()

from setuptools import setup
from pudb import VERSION

import sys
PY_VERSION = str(sys.version_info[0]) if sys.version_info[0] == 3 else ''

with open("README.rst") as readme:
    long_description = str(readme.read())

setup(name='pudb',
      version=VERSION,
      description='A full-screen, console-based Python debugger',
      long_description=long_description,
      author='Andreas Kloeckner',
      author_email='inform@tiker.net',
      install_requires=[
          "urwid>=1.1.1",
          "pygments>=1.0",
          ],
      url='http://pypi.python.org/pypi/pudb',
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Environment :: Console :: Curses",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Natural Language :: English",
          "Operating System :: POSIX",
          "Operating System :: Unix",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 3",
          "Topic :: Software Development",
          "Topic :: Software Development :: Debuggers",
          "Topic :: Software Development :: Quality Assurance",
          "Topic :: System :: Recovery Tools",
          "Topic :: System :: Software Distribution",
          "Topic :: Terminals",
          "Topic :: Utilities",
          ],
      packages=["pudb"],
      entry_points={'console_scripts': ['pudb' + PY_VERSION + ' = pudb.run:main'], 'gui_script': []},
)
