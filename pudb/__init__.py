NUM_VERSION = (2013, 1)
VERSION = ".".join(str(nv) for nv in NUM_VERSION)
__version__ = VERSION

from pudb.py3compat import raw_input


CURRENT_DEBUGGER = []
def _get_debugger(**kwargs):
    if not CURRENT_DEBUGGER:
        from pudb.debugger import Debugger
        dbg = Debugger(**kwargs)

        CURRENT_DEBUGGER.append(dbg)
        return dbg
    else:
        return CURRENT_DEBUGGER[0]

import signal
DEFAULT_SIGNAL = signal.SIGINT
del signal

def runscript(mainpyfile, args=None, pre_run="", steal_output=False):
    dbg = _get_debugger(steal_output=steal_output)

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user from the command line. The best approach would be to
    # have a "restart" command which would allow explicit specification of
    # command line arguments.

    import sys
    if args is not None:
        prev_sys_argv = sys.argv[:]
        sys.argv = [mainpyfile] + args

    # replace pudb's dir with script's dir in front of module search path.
    from os.path import dirname
    prev_sys_path = sys.path[:]
    sys.path[0] = dirname(mainpyfile)

    while True:
        if pre_run:
            from subprocess import call
            retcode = call(pre_run, close_fds=True, shell=True)
            if retcode:
                print("*** WARNING: pre-run process exited with code %d." % retcode)
                raw_input("[Hit Enter]")

        status_msg = ""

        try:
            dbg._runscript(mainpyfile)
        except SystemExit:
            se = sys.exc_info()[1]
            status_msg = "The debuggee exited normally with status code %s.\n\n" % se.code
        except:
            dbg.post_mortem = True
            dbg.interaction(None, sys.exc_info())

        while True:
            import urwid
            pre_run_edit = urwid.Edit("", pre_run)

            result = dbg.ui.call_with_ui(dbg.ui.dialog,
                urwid.ListBox([urwid.Text(
                    "Your PuDB session has ended.\n\n%s"
                    "Would you like to quit PuDB or restart your program?\n"
                    "You may hit 'q' to quit."
                    % status_msg),
                    urwid.Text("\n\nIf you decide to restart, this command will be run prior to "
                    "actually restarting:"),
                    urwid.AttrMap(pre_run_edit, "value")
                    ]),
                [
                    ("Restart", "restart"),
                    ("Examine", "examine"),
                    ("Quit", "quit"),
                    ],
                focus_buttons=True,
                bind_enter_esc=False,
                title="Finished",
                extra_bindings=[
                    ("q", "quit"),
                    ("esc", "examine"),
                    ])

            if result == "quit":
                return

            if result == "examine":
                dbg.post_mortem = True
                dbg.interaction(None, sys.exc_info(), show_exc_dialog=False)

            if result == "restart":
                break

        pre_run = pre_run_edit.get_edit_text()

        dbg.restart()

    if args is not None:
        sys.argv = prev_sys_argv

    sys.path = prev_sys_path

def runstatement(statement, globals=None, locals=None):
    _get_debugger().run(statement, globals, locals)

def runeval(expression, globals=None, locals=None):
    return _get_debugger().runeval(expression, globals, locals)

def runcall(*args, **kwds):
    return _get_debugger().runcall(*args, **kwds)

def set_trace():
    import sys
    dbg = _get_debugger()

    set_interrupt_handler()
    dbg.set_trace(sys._getframe().f_back)


def _interrupt_handler(signum, frame):
    from pudb import _get_debugger
    _get_debugger().set_trace(frame)

def set_interrupt_handler(interrupt_signal=DEFAULT_SIGNAL):
    """
    Set up an interrupt handler, to activate PuDB when Python receives the
    signal `interrupt_signal`.  By default it is SIGINT (i.e., Ctrl-c).

    To use a different signal, pass it as the argument to this function, like
    `set_interrupt_handler(signal.SIGALRM)`.  You can then break your code
    with `kill -ALRM pid`, where `pid` is the process ID of the Python
    process.  Note that PuDB will still use SIGINT once it is running to allow
    breaking running code.  If that is an issue, you can change the default
    signal by hooking `pudb.DEFAULT_SIGNAL`, like

    >>> import pudb
    >>> import signal
    >>> pudb.DEFAULT_SIGNAL = signal.SIGALRM

    Note, this may not work if you use threads or subprocesses.
    """
    import signal
    signal.signal(interrupt_signal, _interrupt_handler)

def post_mortem(exc_info=None):
    if exc_info is None:
        import sys
        exc_info = sys.exc_info()

    tb = exc_info[2]
    while tb.tb_next is not None:
        tb = tb.tb_next

    dbg = _get_debugger()
    dbg.reset()
    dbg.interaction(tb.tb_frame, exc_info)




def pm():
    import sys
    try:
        e_type = sys.last_type
        e_value = sys.last_value
        tb = sys.last_traceback
    except AttributeError:
        ## No exception on record. Do nothing.
        return
    post_mortem((e_type, e_value, tb))




if __name__ == "__main__":
    print("You now need to type 'python -m pudb.run'. Sorry.")
