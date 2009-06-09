#!/usr/bin/env python

from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup

setup(name='pudb',
      version='0.90',
      description='Python Urwid debugger',
      long_description="""
      PuDB is a visual debugger for Python. It runs in the same terminal
      where you run your code. Installing it is as easy as::

          easy_install pudb

      Here's a screenshot:

      .. image:: http://tiker.net/pub/pudb-screenshot.png

      Features
      --------

      Why would you want to use pudb?
      
      * Easy to use!
      * Syntax Highlighting
      * Offers Better situational awareness than CLI-based `pdb`
      * Single keystroke for most commands
      * Self-documenting
      * Set breakpoints visually
      * Easy access to a Python shell
      * Almost as lightweight as Python's included debugger, `pdb`.  

      Getting Started
      ---------------

      To start debugging, simply insert::

          from pudb import set_trace; set_trace()

      into the piece of code you want to debug, or run the entire script with::

          python -m pudb my-script.py

      Getting the Development Version
      -------------------------------

      You may obtain the development version using the `Git <http://git-scm.org/>`_
      version control tool.::

          git clone http://git.tiker.net/trees/pudb.git

      You may also `browse the code <http://git.tiker.net/pudb.git>`_ online.
      """,
      author='Andreas Kloeckner',
      author_email='inform@tiker.net',
      setup_requires=[
          "urwid>=0.9.8.4",
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
      py_modules=["pudb"])

