#!/usr/bin/env python

from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup

setup(name='pudb',
      version='0.90',
      description='Python Urwid debugger',
      author='Andreas Kloeckner',
      author_email='inform@tiker.net',
      requires=[
          "urwid>=0.9.8.4",
          "pygments>=1.0",
          ],
      url='http://pypi.python.org/pypi/pudb',
      py_modules="pudb")

