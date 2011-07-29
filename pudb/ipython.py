import os

try:
    from IPython import ipapi
except ImportError:
    from IPython.frontend.terminal.interactiveshell import \
            TerminalInteractiveShell
    ip = TerminalInteractiveShell.instance()
    _ipython_version = (0, 11)
else:
    ip = ipapi.get()
    _ipython_version = (0, 10)


def pudb_f_v10(self, arg):
    """ Debug a script (like %run -d) in IPython process, using PuDB.

    This conforms to IPython version 0.10

    Usage:

    %pudb test.py [args]
        Run script test.py under PuDB.
    """

    if not arg.strip():
        print __doc__
        return

    from IPython.genutils import arg_split
    args = arg_split(arg)

    path = os.path.abspath(args[0])
    args = args[1:]
    if not os.path.isfile(path):
        raise IPython.ipapi.UsageError("%%pudb: file %s does not exist" % path)

    from pudb import runscript
    ip.IP.history_saving_wrapper(lambda: runscript(path, args))()

def pudb_f_v11(self, arg):
    """ Debug a script (like %run -d) in IPython process, using PuDB.

    This conforms to IPython version 0.11

    Usage:

    %pudb test.py [args]
        Run script test.py under PuDB.
    """

    # Get the running instance

    if not arg.strip():
        print __doc__
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

if _ipython_version == (0, 10):
    ip.expose_magic('pudb', pudb_f_v10)
else:
    ip.define_magic('pudb', pudb_f_v11)
