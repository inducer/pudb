#!/usr/bin/env python

from distribute_setup import use_setuptools

use_setuptools()

from setuptools import setup
from pudb import VERSION

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
          "urwid>=0.9.9.2",
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
          "Topic :: Software Development",
          "Topic :: Software Development :: Debuggers",
          "Topic :: Software Development :: Quality Assurance",
          "Topic :: System :: Recovery Tools",
          "Topic :: System :: Software Distribution",
          "Topic :: Terminals",
          "Topic :: Utilities",
          ],
      packages=["pudb"])

