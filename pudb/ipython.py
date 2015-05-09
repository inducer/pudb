from __future__ import with_statement

import sys
import os

try:
    from IPython import ipapi
    ip = ipapi.get()
    _ipython_version = (0, 10)
except ImportError:
    try:
        from IPython.core.magic import register_line_magic
        from IPython import get_ipython
        _ipython_version = (1, 0)
    except ImportError:
        # Note, keep this run last, or else it will raise a deprecation
        # warning.
        from IPython.frontend.terminal.interactiveshell import \
            TerminalInteractiveShell
        ip = TerminalInteractiveShell.instance()
        _ipython_version = (0, 11)


# This conforms to IPython version 0.10
def pudb_f_v10(self, arg):
    """ Debug a script (like %run -d) in the IPython process, using PuDB.

    Usage:

    %pudb test.py [args]
        Run script test.py under PuDB.
    """

    if not arg.strip():
        print(__doc__)
        return

    from IPython.genutils import arg_split
    args = arg_split(arg)

    path = os.path.abspath(args[0])
    args = args[1:]
    if not os.path.isfile(path):
        raise ipapi.UsageError("%%pudb: file %s does not exist" % path)

    from pudb import runscript
    ip.IP.history_saving_wrapper(lambda: runscript(path, args))()


# This conforms to IPython version 0.11
def pudb_f_v11(self, arg):
    """ Debug a script (like %run -d) in the IPython process, using PuDB.

    Usage:

    %pudb test.py [args]
        Run script test.py under PuDB.
    """

    # Get the running instance

    if not arg.strip():
        print(pudb_f_v11.__doc__)
        return

    from IPython.utils.process import arg_split
    args = arg_split(arg)

    path = os.path.abspath(args[0])
    args = args[1:]
    if not os.path.isfile(path):
        from IPython.core.error import UsageError
        raise UsageError("%%pudb: file %s does not exist" % path)

    from pudb import runscript
    runscript(path, args)


if _ipython_version == (1, 0):
    # For IPython 1.0.0
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
        """
        Call the PuDB debugger
        """
        from IPython.utils.warn import error
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

elif _ipython_version == (0, 10):
    ip.expose_magic('pudb', pudb_f_v10)
else:
    ip.define_magic('pudb', pudb_f_v11)
