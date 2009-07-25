import os
import IPython.ipapi
import pudb

ip = IPython.ipapi.get()

def pudb_f(self, arg):
    """ Debug a script (like %run -d) in IPython process, using PuDB.

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

ip.expose_magic('pudb', pudb_f)
