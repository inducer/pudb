#!/usr/bin/env python

from setuptools import find_packages, setup

from pudb import VERSION


with open("README.rst") as readme:
    long_description = str(readme.read())

setup(
    name="pudb",
    version=VERSION,
    description="A full-screen, console-based Python debugger",
    long_description=long_description,
    author="Andreas Kloeckner",
    author_email="inform@tiker.net",
    python_requires="~=3.8",
    install_requires=[
        "urwid>=2.4",
        "pygments>=2.7.4",
        "jedi>=0.18,<1",
        "urwid_readline",
        "packaging>=20.0",
    ],
    extras_require={"completion": ["shtab"]},
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
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            # Deprecated. Should really use python -m pudb.
            "pudb = pudb.run:main",
            ],
        "gui_script": [],
    },
)
