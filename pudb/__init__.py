from __future__ import annotations


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
import re
import sys
from importlib import metadata
from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import ParamSpec

from pudb.settings import load_config


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from types import TracebackType

    from pudb.debugger import Debugger


P = ParamSpec("P")
ResultT = TypeVar("ResultT")


VERSION = metadata.version("pudb")
_ver_match = re.match(r"^([0-9.]+)([a-z0-9]*?)$", VERSION)
assert _ver_match
NUM_VERSION = tuple(int(nr) for nr in _ver_match.group(1).split("."))
__version__ = VERSION


class PudbShortcuts:
    @property
    def db(self):
        dbg = _get_debugger()

        import threading
        if isinstance(threading.current_thread(), threading._MainThread):
            set_interrupt_handler()
        dbg.set_trace(sys._getframe().f_back)

    @property
    def go(self):
        dbg = _get_debugger()

        import threading
        if isinstance(threading.current_thread(), threading._MainThread):
            set_interrupt_handler()
        dbg.set_trace(sys._getframe().f_back, paused=False)


import builtins


builtins.__dict__["pu"] = PudbShortcuts()


def _tty_override():
    import os
    return os.environ.get("PUDB_TTY")


def _open_tty(tty_path: str):
    import io
    import os
    tty_file = io.TextIOWrapper(open(tty_path, "r+b", buffering=0))
    term_size = os.get_terminal_size(tty_file.fileno())

    return tty_file, term_size


def _get_debugger(**kwargs):
    from pudb.debugger import Debugger
    if not Debugger._current_debugger:
        tty_path = _tty_override()
        if tty_path and ("stdin" not in kwargs or "stdout" not in kwargs):
            tty_file, term_size = _open_tty(tty_path)
            kwargs.setdefault("stdin", tty_file)
            kwargs.setdefault("stdout", tty_file)
            kwargs.setdefault("term_size", term_size)
            kwargs.setdefault("tty_file", tty_file)

        from pudb.debugger import Debugger
        dbg = Debugger(**kwargs)

        return dbg
    else:
        return Debugger._current_debugger[0]


def _have_debugger():
    try:
        from pudb.debugger import Debugger
        return bool(Debugger._current_debugger)
    except ImportError:
        # Import cycles may happen if function is called during early startup
        return False


import signal  # noqa
DEFAULT_SIGNAL = signal.SIGINT
del signal


def runmodule(*args, **kwargs):
    kwargs["run_as_module"] = True
    runscript(*args, **kwargs)


def runscript(
            mainpyfile: str,
            steal_output: bool = False,
            _continue_at_start: bool = False,
            args: Sequence[str] | None = None,
            pre_run: str = "",
            run_as_module: bool = False,
        ):
    try:
        dbg = _get_debugger(
            steal_output=steal_output,
            _continue_at_start=_continue_at_start,
        )
        _runscript(mainpyfile, dbg,
                   args=args, pre_run=pre_run, run_as_module=run_as_module)
    finally:
        dbg.__del__()


def _runscript(
            mainpyfile: str,
            dbg: Debugger,
            args: Sequence[str] | None = None,
            pre_run: str = "",
            run_as_module: bool = False,
        ):

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user from the command line. The best approach would be to
    # have a "restart" command which would allow explicit specification of
    # command line arguments.

    if args is not None:
        prev_sys_argv = sys.argv[:]
        if run_as_module:
            sys.argv = args
        else:
            sys.argv = [mainpyfile, *args]

    # replace pudb's dir with script's dir in front of module search path.
    from pathlib import Path
    prev_sys_path = sys.path[:]
    sys.path[0] = str(Path(mainpyfile).resolve().parent)

    import os
    cwd = os.getcwd()

    while True:
        # Script may have changed directory. Restore cwd before restart.
        os.chdir(cwd)

        if pre_run:
            from subprocess import call
            retcode = call(pre_run, close_fds=True, shell=True)
            if retcode:
                print("*** WARNING: pre-run process exited with code %d." % retcode)
                input("[Hit Enter]")

        status_msg = ""

        try:
            if run_as_module:
                try:
                    dbg._runmodule(mainpyfile)
                except ImportError as e:
                    print(e, file=sys.stderr)
                    sys.exit(1)
            else:
                try:
                    dbg._runscript(mainpyfile)
                except SystemExit:
                    se = sys.exc_info()[1]
                    status_msg = "The debuggee exited normally with " \
                            f"status code {se.code}.\n\n"
        except Exception:
            dbg.post_mortem = True
            dbg.interaction(None, sys.exc_info())

        while True:
            import urwid
            pre_run_edit = urwid.Edit("", pre_run)

            if not load_config()["prompt_on_quit"]:
                return

            result = dbg.ui.call_with_ui(dbg.ui.dialog,
                urwid.ListBox(urwid.SimpleListWalker([urwid.Text(
                    f"Your PuDB session has ended.\n\n{status_msg}"
                    "Would you like to quit PuDB or restart your program?\n"
                    "You may hit 'q' to quit."),
                    urwid.Text("\n\nIf you decide to restart, this command "
                    "will be run prior to actually restarting:"),
                    urwid.AttrMap(pre_run_edit, "input", "focused input")
                    ])),
                [
                    ("Restart", "restart"),
                    ("Quit", "quit"),
                    ],
                focus_buttons=True,
                bind_enter_esc=False,
                title="Finished",
                extra_bindings=[
                    ("q", "quit"),
                    ])

            if result == "quit":
                return

            if result == "restart":
                break

        pre_run = pre_run_edit.get_edit_text()

        dbg.restart()

    if args is not None:
        sys.argv = prev_sys_argv

    sys.path = prev_sys_path


def runstatement(
            statement: str,
            globals: dict[str, Any] | None = None,
            locals: Mapping[str, Any] | None = None
        ):
    return _get_debugger().run(statement, globals, locals)


def runeval(expression, globals=None, locals=None):
    return _get_debugger().runeval(expression, globals, locals)


def runcall(
            func: Callable[P, ResultT],
            *args: P.args,
            **kwargs: P.kwargs
        ) -> ResultT | None:
    return _get_debugger().runcall(func, *args, **kwargs)


def set_trace(paused: bool = True):
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


def set_interrupt_handler(interrupt_signal=None):
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

    if interrupt_signal is None:
        interrupt_signal = DEFAULT_SIGNAL

    import signal
    old_handler = signal.getsignal(interrupt_signal)

    if old_handler is not signal.default_int_handler \
            and old_handler != signal.SIG_DFL and old_handler != _interrupt_handler:
        # Since we don't currently have support for a non-default signal handlers,
        # let's avoid undefined-behavior territory and just show a warning.
        from warnings import warn
        if old_handler is None:
            # This is the documented meaning of getsignal()->None.
            old_handler = "not installed from python"
        return warn("A non-default handler for signal %d is already installed (%s). "
                "Skipping pudb interrupt support."
                % (interrupt_signal, old_handler),
                stacklevel=2)

    import threading
    if not isinstance(threading.current_thread(), threading._MainThread):
        from warnings import warn
        # Setting signals from a non-main thread will not work
        return warn("Setting the interrupt handler can only be done on the main "
                "thread. The interrupt handler was NOT installed.",
                stacklevel=2)

    try:
        signal.signal(interrupt_signal, _interrupt_handler)
    except ValueError:
        import sys
        from traceback import format_exception
        from warnings import warn
        warn("setting interrupt handler on signal %d failed: %s"
                % (interrupt_signal, "".join(format_exception(*sys.exc_info()))),
                stacklevel=2)


def post_mortem(
            tb: TracebackType | None = None,
            e_type: type[BaseException] | None = None,
            e_value: BaseException | None = None):
    if tb is None:
        import sys
        exc_info = sys.exc_info()
    else:
        assert e_type is not None
        assert e_value is not None
        exc_info = (e_type, e_value, tb)

    dbg = _get_debugger()
    dbg.reset()
    dbg.interaction(None, exc_info)


def pm():
    import sys
    exc_type, _exc_val, _tb = sys.exc_info()

    if exc_type is None:
        # No exception on record. Do nothing.
        return
    post_mortem()


if __name__ == "__main__":
    print("You now need to type 'python -m pudb.run'. Sorry.")

# vim: foldmethod=marker:expandtab:softtabstop=4
