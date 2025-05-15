from __future__ import annotations

import os
import sys

from pudb.debugger import Debugger


def set_trace(paused=True, frame=None, term_size=None):
    """Set a breakpoint in a forked process on Unix system, e.g. Linux & MacOS.
    In- and output will be redirected to /dev/stdin & /dev/stdout.
    You can call pudb.forked.set_trace() directly or
    use it with python's built-in breakpoint():
    PYTHONBREAKPOINT=pudb.forked.set_trace python …
    """
    if frame is None:
        frame = sys._getframe().f_back
    if term_size is None:
        term_size = os.environ.get("PUDB_TERM_SIZE")
        if term_size is not None:
            term_size = tuple(map(int, term_size.split("x")))
            if len(term_size) != 2:
                raise ValueError("PUDB_TERM_SIZE should have two dimensions")
        else:
            try:
                # Getting terminal size
                s = os.get_terminal_size()
                term_size = (s.columns, s.lines)
            except Exception:
                term_size = (80, 24)

    Debugger(
        stdin=open("/dev/stdin"),
        stdout=open("/dev/stdout", "w"),
        term_size=term_size,
    ).set_trace(frame, paused=paused)
