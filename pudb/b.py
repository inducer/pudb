from __future__ import annotations

import sys

from pudb import _get_debugger, set_interrupt_handler


def __myimport__(name, *args, **kwargs):  # noqa: N807
    if name == "pudb.b":
        set_trace()
    return __origimport__(name, *args, **kwargs)  # noqa: F821 # pylint: disable=undefined-variable


# Will only be run on first import
__builtins__["__origimport__"] = __import__
__builtins__["__import__"] = __myimport__


def set_trace():
    dbg = _get_debugger()
    set_interrupt_handler()
    dbg.set_trace(sys._getframe().f_back.f_back)


set_trace()
