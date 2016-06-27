#!/usr/bin/env python

from setuptools import setup
from pudb import VERSION

import sys
py_version_major = sys.version_info[0]
if py_version_major == 3:
    PY_VERSION = str(py_version_major)
else:
    PY_VERSION = ''

try:
    readme = open("README.rst")
    long_description = str(readme.read())
finally:
    readme.close()

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
      test_requires=[
          "pytest>=2",
          ],
      url='https://github.com/inducer/pudb',
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
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Topic :: Software Development",
          "Topic :: Software Development :: Debuggers",
          "Topic :: Software Development :: Quality Assurance",
          "Topic :: System :: Recovery Tools",
          "Topic :: System :: Software Distribution",
          "Topic :: Terminals",
          "Topic :: Utilities",
          ],
      packages=["pudb"],
      entry_points={
          'console_scripts': ['pudb' + PY_VERSION + ' = pudb.run:main'],
          'gui_script': []},
      )
