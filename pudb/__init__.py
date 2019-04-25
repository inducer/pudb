from __future__ import absolute_import, division, print_function

__copyright__ = """
Copyright (C) 2009-2017 Andreas Kloeckner
Copyright (C) 2014-2017 Aaron Meurer
"""

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


NUM_VERSION = (2019, 1)
VERSION = ".".join(str(nv) for nv in NUM_VERSION)
__version__ = VERSION

from pudb.py3compat import raw_input, PY3

from pudb.settings import load_config, save_config
CONFIG = load_config()
save_config(CONFIG)


class PudbShortcuts(object):
    @property
    def db(self):
        import sys
        dbg = _get_debugger()

        import threading
        if isinstance(threading.current_thread(), threading._MainThread):
            set_interrupt_handler()
        dbg.set_trace(sys._getframe().f_back)

    @property
    def go(self):
        import sys
        dbg = _get_debugger()

        import threading
        if isinstance(threading.current_thread(), threading._MainThread):
            set_interrupt_handler()
        dbg.set_trace(sys._getframe().f_back, paused=False)


if PY3:
    import builtins
    builtins.__dict__["pu"] = PudbShortcuts()
else:
    import __builtin__
    __builtin__.__dict__["pu"] = PudbShortcuts()


CURRENT_DEBUGGER = []


def _tty_override():
    import os
    return os.environ.get('PUDB_TTY')


def _open_tty(tty_path):
    import io
    import os
    import sys
    if sys.version_info[0] == 2:
        tty_file = open(tty_path, 'r+b', buffering=0)
        term_size = None
    else:
        tty_file = io.TextIOWrapper(open(tty_path, 'r+b', buffering=0))
        term_size = os.get_terminal_size(tty_file.fileno())

    return tty_file, term_size


def _get_debugger(**kwargs):
    if not CURRENT_DEBUGGER:
        tty_path = _tty_override()
        if tty_path and ('stdin' not in kwargs or 'stdout' not in kwargs):
            tty_file, term_size = _open_tty(tty_path)

            kwargs.setdefault('stdin', tty_file)
            kwargs.setdefault('stdout', tty_file)
            kwargs.setdefault('term_size', term_size)

        from pudb.debugger import Debugger
        dbg = Debugger(**kwargs)

        CURRENT_DEBUGGER.append(dbg)
        return dbg
    else:
        return CURRENT_DEBUGGER[0]


import signal  # noqa
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
            status_msg = "The debuggee exited normally with " \
                    "status code %s.\n\n" % se.code
        except Exception:
            dbg.post_mortem = True
            dbg.interaction(None, sys.exc_info())

        while True:
            import urwid
            pre_run_edit = urwid.Edit("", pre_run)

            if not CONFIG["prompt_on_quit"]:
                return

            result = dbg.ui.call_with_ui(dbg.ui.dialog,
                urwid.ListBox(urwid.SimpleListWalker([urwid.Text(
                    "Your PuDB session has ended.\n\n%s"
                    "Would you like to quit PuDB or restart your program?\n"
                    "You may hit 'q' to quit."
                    % status_msg),
                    urwid.Text("\n\nIf you decide to restart, this command "
                    "will be run prior to actually restarting:"),
                    urwid.AttrMap(pre_run_edit, "value")
                    ])),
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


def set_trace(paused=True):
    """
    Start the debugger

    If paused=False (the default is True), the debugger will not stop here
    (same as immediately pressing 'c' to continue).
    """
    import sys
    dbg = _get_debugger()

    import threading
    if isinstance(threading.current_thread(), threading._MainThread):
        set_interrupt_handler()

    dbg.set_trace(sys._getframe().f_back, paused=paused)


start = set_trace


def _interrupt_handler(signum, frame):
    from pudb import _get_debugger
    _get_debugger().set_trace(frame, as_breakpoint=False)


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

    Note, this only works when called from the main thread.
    """
    import signal
    old_handler = signal.getsignal(interrupt_signal)

    if old_handler is not signal.default_int_handler \
            and old_handler != signal.SIG_DFL and old_handler != _interrupt_handler:
        # Since we don't currently have support for a non-default signal handlers,
        # let's avoid undefined-behavior territory and just show a warning.
        from warnings import warn
        if old_handler is None:
            # This is the documented meaning of getsignal()->None.
            old_handler = 'not installed from python'
        return warn("A non-default handler for signal %d is already installed (%s). "
                "Skipping pudb interrupt support."
                % (interrupt_signal, old_handler))

    import threading
    if not isinstance(threading.current_thread(), threading._MainThread):
        from warnings import warn
        # Setting signals from a non-main thread will not work
        return warn("Setting the interrupt handler can only be done on the main "
                "thread. The interrupt handler was NOT installed.")

    try:
        signal.signal(interrupt_signal, _interrupt_handler)
    except ValueError:
        from pudb.lowlevel import format_exception
        import sys
        from warnings import warn
        warn("setting interrupt handler on signal %d failed: %s"
                % (interrupt_signal, "".join(format_exception(sys.exc_info()))))


def post_mortem(tb=None, e_type=None, e_value=None):
    if tb is None:
        import sys
        exc_info = sys.exc_info()
    else:
        exc_info = (e_type, e_value, tb)

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
        # No exception on record. Do nothing.
        return
    post_mortem(tb, e_type, e_value)


if __name__ == "__main__":
    print("You now need to type 'python -m pudb.run'. Sorry.")

# vim: foldmethod=marker:expandtab:softtabstop=4
