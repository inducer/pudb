#!/usr/bin/env python

from setuptools import setup
from pudb import VERSION

import sys

try:
    readme = open("README.rst")
    long_description = str(readme.read())
finally:
    readme.close()

setup(
    name="pudb",
    version=VERSION,
    description="A full-screen, console-based Python debugger",
    long_description=long_description,
    author="Andreas Kloeckner",
    author_email="inform@tiker.net",
    python_requires="~=3.6",
    install_requires=[
        "urwid>=1.1.1",
        "pygments>=2.7.4",
        "jedi>=0.18,<1",
        "urwid_readline",
        "packaging>=20.0",
        "dataclasses>=0.7;python_version<'3.7'",
    ],
    test_requires=[
        "pytest>=2",
        "pytest-mock",
    ],
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
    entry_points={
        "console_scripts": [
            # Deprecated. Should really use python -m pudb.
            "pudb3 = pudb.run:main",
            ],
        "gui_script": [],
    },
)
