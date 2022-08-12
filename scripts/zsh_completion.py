#!/usr/bin/env python
import os
from os.path import dirname as dirn
import sys
import re
from setuptools import find_packages
from argparse import SUPPRESS
from typing import Final

path = dirn(dirn((os.path.abspath(__file__))))
sys.path.insert(0, path)
from pudb.run import get_argparse_parser

PACKAGES: Final = find_packages(path)
PACKAGE: Final = PACKAGES[0]
BINNAME: Final = "pudb3"
ZSH_COMPLETION_FILE: Final = "_" + BINNAME
ZSH_COMPLETION_TEMPLATE: Final = os.path.join(
    dirn(os.path.abspath(__file__)), "zsh_completion.in"
)
pat_class = re.compile("'(.*)'")

flags = []
for action in get_argparse_parser()._actions:
    if len(action.option_strings) > 1:
        optionstr = "{" + ",".join(action.option_strings) + "}"
    elif len(action.option_strings) == 1:
        optionstr = action.option_strings[0]
    else:
        optionstr = ""
    if action.dest in ["help", "version"]:
        prefix = "'(- *)'"
    else:
        prefix = ""

    if action.help == SUPPRESS:
        helpstr = ""
    elif action.help:
        helpstr = action.help.replace("]", "\\]").replace("'", "'\\''")
    else:
        helpstr = ""
    if optionstr == "":
        flag = "'(-)1"
    else:
        flag = "{0}{1}'[{2}]".format(prefix, optionstr, helpstr)
    if action.metavar is None and optionstr == "":
        action.metavar = action.dest
    if isinstance(action.metavar, str):
        completion = ":" + action.metavar.replace(":", "\\:")
        action.metavar = action.metavar.lower()
        if action.metavar == "file":
            completion += ":_files"
        elif action.metavar == "script_args":
            completion += ":_files -g *.py"
        elif action.metavar == "dir":
            completion += ":_dirs"
        elif action.metavar == "url":
            completion += ":_urls"
    elif isinstance(action.default, bool) or action.default == SUPPRESS:
        completion = ""
    else:
        completion = ":" + pat_class.findall(str(action.default.__class__))[0]
    if action.choices:
        completion += ":(" + " ".join(action.choices) + ")"
    flags += ["{0}{1}'".format(flag, completion)]

with open(ZSH_COMPLETION_TEMPLATE) as f:
    template = f.read()

template = template.replace("{{programs}}", BINNAME)
template = template.replace("{{flags}}", " \\\n  ".join(flags))

with open(ZSH_COMPLETION_FILE, "w") as f:
    f.write(template)
