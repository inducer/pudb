from __future__ import absolute_import, division, print_function, with_statement

import sys
import os

from IPython.core.magic import register_line_magic
from IPython import get_ipython


def pudb(line):
    """
    Debug a script (like %run -d) in the IPython process, using PuDB.

    Usage:

    %pudb test.py [args]
        Run script test.py under PuDB.
    """

    # Get the running instance

    if not line.strip():
        print(pudb.__doc__)
        return

    from IPython.utils.process import arg_split
    args = arg_split(line)

    path = os.path.abspath(args[0])
    args = args[1:]
    if not os.path.isfile(path):
        from IPython.core.error import UsageError
        raise UsageError("%%pudb: file %s does not exist" % path)

    from pudb import runscript
    runscript(path, args)


register_line_magic(pudb)


def debugger(self, force=False):
    """Call the PuDB debugger."""
    from logging import error
    if not (force or self.call_pdb):
        return

    if not hasattr(sys, 'last_traceback'):
        error('No traceback has been produced, nothing to debug.')
        return

    from pudb import pm

    with self.readline_no_record:
        pm()


ip = get_ipython()
ip.__class__.debugger = debugger
