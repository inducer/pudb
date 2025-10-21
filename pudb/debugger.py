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


import bdb
import gc
import os
import sys
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from functools import partial
from itertools import count
from os.path import splitext
from types import FrameType, ModuleType, TracebackType
from typing import TYPE_CHECKING, Any, ClassVar, Mapping, TextIO, TypeVar, cast, final

import urwid
from typing_extensions import ParamSpec, TypeAlias, override

from pudb.lowlevel import ConsoleSingleKeyReader, decode_lines, ui_log
from pudb.settings import get_save_config_path, load_config, save_config


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pudb.source_view import SourceLine


P = ParamSpec("P")
ResultT = TypeVar("ResultT")

ExcInfo: TypeAlias = "tuple[type[BaseException], BaseException, TracebackType]"
OptExcInfo: TypeAlias = "ExcInfo | tuple[None, None, None]"


CONFIG = load_config()
save_config(CONFIG)

HELP_HEADER = r"""
Key Assignments: Use Arrow Down/Up or Page Down/Up to scroll.
"""

HELP_MAIN = rf"""
Keys:
    Ctrl-p - edit preferences

    n - step over ("next")
    s - step into
    c - continue
    r/f - finish current function
    t - run to cursor
    J - jump to line
    e - show traceback [post-mortem or in exception state]
    b - set/clear breakpoint
    Ctrl-e - open file at current line to edit with $EDITOR

    H - move to current line (bottom of stack)
    u - move up one stack frame
    d - move down one stack frame

    o - show console/output screen
    m - open module

    j/k - down/up
    l/h - right/left
    Ctrl-f/b - page down/up
    Ctrl-d/u - page down/up
    G/g - end/home

    L - show (file/line) location / go to line
    / - search
    ,/. - search next/previous

    {CONFIG["hotkeys_variables"]} - focus variables
    {CONFIG["hotkeys_stack"]} - focus stack
    {CONFIG["hotkeys_breakpoints"]} - focus breakpoint list
    {CONFIG["hotkeys_code"]} - focus code

    F1/? - show this help screen
    q - quit

    Ctrl-r - reload breakpoints from saved-breakpoints file
    Ctrl-c - when in continue mode, break back to PuDB
    Ctrl-l - redraw screen

Shell-related:
    ! - open the external shell (configured in the settings)
    {CONFIG["hotkeys_toggle_cmdline_focus"]} - toggle the internal shell focus

    +/- - grow/shrink inline shell (active in results scrollback)
    _/= - minimize/maximize inline shell (active in results scrollback)

    Ctrl-v - insert newline
    Ctrl-n/p, Arrow down/up - browse command history or clear/recall prompt
    Shift-Page down/up - browse in the results scrollback
    Tab - yes, there is (simple) tab completion
"""

HELP_SIDE = rf"""
Sidebar-related (active in sidebar):
    +/- - grow/shrink sidebar width
    _/= - minimize/maximize sidebar width
    [/] - grow/shrink relative height of active sidebar box

Keys in variables list:
    \/enter/space - expand/collapse
    h - collapse
    l - expand
    d/t/r/s/i/c - show default/type/repr/str/id/custom for this variable
    H - toggle highlighting
    @ - toggle repetition at top
    * - cycle attribute visibility: public/_private/__dunder__
    m - toggle method visibility
    w - toggle line wrapping
    n/insert - add new watch expression
    delete - remove watch expression
    e - edit options

Keys in stack list:
    enter - jump to frame
    Ctrl-e - open file at line to edit with $EDITOR

Keys in breakpoints list:
    enter - jump to breakpoint
    b - toggle breakpoint
    d - delete breakpoint
    e - edit breakpoint

Other keys:
    j/k - down/up
    l/h - right/left
    Ctrl-f/b - page down/up
    Ctrl-d/u - page down/up
    G/g - end/home

    {CONFIG["hotkeys_variables"]} - focus variables
    {CONFIG["hotkeys_stack"]} - focus stack
    {CONFIG["hotkeys_breakpoints"]} - focus breakpoint list
    {CONFIG["hotkeys_code"]} - focus code

    F1/? - show this help screen
    q - quit

    Ctrl-l - redraw screen
"""

HELP_LICENSE = r"""
License:
--------

PuDB is licensed to you under the MIT/X Consortium license:

Copyright (c) 2009-16 Andreas Kloeckner and contributors

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""


def mod_exists(mod: ModuleType):
    if not hasattr(mod, "__file__"):
        return False
    if mod.__file__ is None:
        return False
    filename = mod.__file__

    base, ext = splitext(filename)
    ext = ext.lower()

    from os.path import exists

    if ext == ".pyc":
        return exists(base+".py")
    else:
        return ext == ".py"


def pick_module(ui: DebuggerUI, w: urwid.Widget, _size: UrwidSize, _key: str):
    import sys

    new_mod_text = SelectableText("-- update me --")
    new_mod_entry = urwid.AttrMap(new_mod_text,
            None, "focused selectable")

    def build_filtered_mod_list(filt_string: str = ""):
        modules = sorted(name
                # mod_exists may change the size of sys.modules,
                # causing this to crash. Copy to a list.
                for name, mod in list(sys.modules.items())
                if mod_exists(mod))

        result = [urwid.AttrMap(SelectableText(mod),
                None, "focused selectable")
                for mod in modules if filt_string in mod]
        new_mod_text.set_text(f"<<< IMPORT MODULE '{filt_string}' >>>")
        result.append(new_mod_entry)
        return result

    def show_mod(mod: ModuleType):
        assert mod.__file__ is not None
        filename = ui.debugger.canonic(mod.__file__)

        base, ext = splitext(filename)
        if ext == ".pyc":
            ext = ".py"
            filename = base+".py"

        ui.set_source_code_provider(
                FileSourceCodeProvider(ui.debugger, filename))
        ui.source_list.set_focus(0)

    class FilterEdit(urwid.Edit):
        @override
        def keypress(self, size: UrwidSize, key: str):
            # type ignore because of urwid annotation bug
            result = urwid.Edit.keypress(self, size, key)  # pyright: ignore[reportArgumentType]

            if result is None:
                mod_list[:] = build_filtered_mod_list(
                        self.get_edit_text())

            return result

    filt_edit = FilterEdit([("label", "Filter: ")],
            ui.last_module_filter)

    mod_list = urwid.SimpleListWalker(
            build_filtered_mod_list(filt_edit.get_edit_text()))
    lb = urwid.ListBox(mod_list)

    w = urwid.Pile([
        (urwid.PACK, urwid.AttrMap(filt_edit, "input", "focused input")),
        (1, urwid.SolidFill()),
        urwid.AttrMap(lb, "selectable")])

    while True:
        result = ui.dialog(w, [
            ("OK", True),
            ("Cancel", False),
            ("Reload", "reload"),

            ], title="Pick Module")
        ui.last_module_filter = filt_edit.get_edit_text()

        widget = cast("urwid.AttrMap[SelectableText]", lb.focus)
        if result is True:
            pos = lb.focus_position
            base_widget = widget.base_widget
            assert isinstance(base_widget, SelectableText)
            if widget is new_mod_entry:
                new_mod_name = filt_edit.get_edit_text()
                try:
                    __import__(str(new_mod_name))
                except Exception:
                    from traceback import format_exception

                    ui.message(
                            "Could not import module '{}':\n\n{}".format(
                                new_mod_name, "".join(
                                    format_exception(*sys.exc_info()))),
                            title="Import Error")
                else:
                    show_mod(__import__(str(new_mod_name)))
                    break
            else:
                show_mod(sys.modules[cast("str", base_widget.get_text()[0])])
                break
        elif result is False:
            break
        elif result == "reload":
            pos = lb.focus_position
            base_widget = widget.base_widget
            assert isinstance(base_widget, SelectableText)
            if widget is not new_mod_entry:
                mod_name = cast("str", base_widget.get_text()[0])
                mod = sys.modules[mod_name]
                import importlib
                importlib.reload(mod)

                ui.message(f"'{mod_name}' was successfully reloaded.")

                if ui.source_code_provider is not None:
                    ui.source_code_provider.clear_cache()

                assert ui.source_code_provider
                ui.set_source_code_provider(ui.source_code_provider,
                        force_update=True)

                pos = ui.stack_list._w.focus_position
                ui.debugger.set_frame_index(
                        ui.translate_ui_stack_index(pos))


# {{{ debugger interface

class Debugger(bdb.Bdb):
    _current_debugger: ClassVar[list[Debugger]] = []
    ui: DebuggerUI

    # FIXME: Explain the distinction between these two
    botframe: FrameType | None
    bottom_frame: FrameType | None

    enterframe: FrameType | None  # pyright: ignore[reportUninitializedInstanceVariable]

    steal_output: bool
    _continue_at_start__setting: bool
    _tty_file: TextIO | None

    curindex: int  # pyright: ignore[reportUninitializedInstanceVariable]

    current_line: SourceLine  # pyright: ignore[reportUninitializedInstanceVariable]

    def __init__(self,
                stdin: TextIO | None = None,
                stdout: TextIO | None = None,
                term_size: tuple[int, int] | None = None,
                steal_output: bool = False,
                _continue_at_start: bool = False,
                tty_file: TextIO | None = None,
                **kwargs: Any):

        if Debugger._current_debugger:
            raise ValueError("a Debugger instance already exists")

        # Pass remaining kwargs to python debugger framework
        bdb.Bdb.__init__(self, **kwargs)
        self.ui = DebuggerUI(self, stdin=stdin, stdout=stdout, term_size=term_size)
        self.steal_output = steal_output
        self._continue_at_start__setting = _continue_at_start
        self._tty_file = tty_file

        self.setup_state()

        if steal_output:
            raise NotImplementedError("output stealing")
            from io import StringIO
            self.stolen_output = sys.stderr = sys.stdout = StringIO()
            sys.stdin = StringIO("")  # avoid spurious hangs

        from pudb.settings import load_breakpoints
        for bpoint_descr in load_breakpoints():
            self.set_break(*bpoint_descr)

        # Okay, now we have a debugger
        self._current_debugger.append(self)

    def __del__(self):
        # according to https://stackoverflow.com/a/1481512/1054322, the garbage
        # collector cannot be relied on to  call this, so we call it explicitly
        # in a finally (see __init__.py:runscript). But then, the garbage
        # collector *might* call it, so it should tolerate being called twice.

        if self._current_debugger:
            assert self._current_debugger == [self]
            self._current_debugger.pop()
        if self._tty_file:
            self._tty_file.close()
            self._tty_file = None

    def set_jump(self, frame: FrameType, line: int):
        frame.f_lineno = line  # pyright: ignore[reportAttributeAccessIssue]

    @override
    def set_trace(self,
                frame: FrameType | None = None,
                as_breakpoint: bool | None = None,
                paused: bool = True,
            ):
        """Start debugging from `frame`.

        If frame is not specified, debugging starts from caller's frame.

        Unlike Bdb.set_trace(), this does not call self.reset(), which causes
        the debugger to enter bdb source code. This also implements treating
        set_trace() calls as breakpoints in the PuDB UI.

        If as_breakpoint=True (the default), this call will be treated like a
        breakpoint in the UI (you can press 'b' on it to disable breaking
        here).

        If paused=False, the debugger will not break here.
        """
        if as_breakpoint is None:
            if not paused:
                as_breakpoint = False
            else:
                as_breakpoint = True

        if frame is None:
            frame = sys._getframe().f_back
            assert frame is not None

        # See pudb issue #52. If this works well enough we should upstream to
        # stdlib bdb.py.
        # self.reset()
        self.enterframe = frame

        thisframe = frame
        while thisframe:
            thisframe.f_trace = self.trace_dispatch
            self.botframe = thisframe
            if sys.version_info >= (3, 13):
                # save trace flags, to be restored by set_continue
                self.frame_trace_lines_opcodes[thisframe] = (  # pylint: disable=no-member
                    thisframe.f_trace_lines,
                    thisframe.f_trace_opcodes)

                # We need f_trace_lines == True for the debugger to work
                thisframe.f_trace_lines = True

            thisframe = thisframe.f_back

        frame_info = (self.canonic(frame.f_code.co_filename), frame.f_lineno)
        if frame_info not in self.set_traces or self.set_traces[frame_info]:
            if as_breakpoint:
                self.set_traces[frame_info] = True
                if self.ui.source_code_provider is not None:
                    self.ui.set_source_code_provider(
                            self.ui.source_code_provider, force_update=True)

            if paused:
                self._set_stopinfo(frame, None)
            else:
                self.set_continue()
            sys.settrace(self.trace_dispatch)
        else:
            return

    def save_breakpoints(self):
        from pudb.settings import save_breakpoints
        save_breakpoints([
            bp
            for fn, bp_lst in self.get_all_breaks().items()
            for lineno in bp_lst
            for bp in self.get_breaks(fn, lineno)
            if not bp.temporary])

    def enter_post_mortem(self, exc_tuple):
        self.post_mortem = True

    def setup_state(self):
        self.bottom_frame = None
        self.mainpyfile = ""
        self._wait_for_mainpyfile = False
        self._continue_at_start = self._continue_at_start__setting
        self.current_bp = None
        self.post_mortem = False
        # Mapping of (filename, lineno) to bool. If True, will stop on the
        # set_trace() call at that location.
        self.set_traces = {}

    def restart(self):
        from linecache import checkcache
        checkcache()
        self.ui.set_source_code_provider(NullSourceCodeProvider())
        self.setup_state()

    def do_clear(self, arg):
        self.clear_bpbynumber(int(arg))

    def set_frame_index(self, index: int):
        self.curindex = index
        if index < 0 or index >= len(self.stack):
            return

        self.curframe, lineno = self.stack[index]

        filename = self.curframe.f_code.co_filename

        import linecache
        if not linecache.getlines(filename):
            code = cast("str | None",
                        self.curframe.f_globals.get("_MODULE_SOURCE_CODE"))
            if code is not None:
                self.ui.set_current_line(lineno,
                        DirectSourceCodeProvider(
                            self.curframe.f_code.co_name, code))
            else:
                self.ui.set_current_line(lineno,
                        NullSourceCodeProvider())

        else:
            self.ui.set_current_line(lineno,
                FileSourceCodeProvider(self, filename))

        self.ui.update_var_view()
        self.ui.update_stack()

        self.ui.stack_list._w.set_focus(self.ui.translate_ui_stack_index(index))

    @staticmethod
    def open_file_to_edit(filename, line_number):
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"'{filename}' not found or is not a file.")

        if not line_number:
            line_number = 1

        editor = os.environ.get("EDITOR", "nano")

        import subprocess
        subprocess.call([editor, f"+{line_number}", filename], shell=False)

        return filename

    def move_up_frame(self):
        if self.curindex > 0:
            self.set_frame_index(self.curindex-1)

    def move_down_frame(self):
        if self.curindex < len(self.stack)-1:
            self.set_frame_index(self.curindex+1)

    def get_shortened_stack(self, frame, tb):
        if tb is not None:
            frame = None
        stack, index = self.get_stack(frame, tb)

        for i, (s_frame, _lineno) in enumerate(stack):
            if s_frame is self.bottom_frame and index >= i:
                stack = stack[i:]
                index -= i

        return stack, index

    def interaction(self,
                frame: FrameType | None,
                exc_tuple: TracebackType | OptExcInfo | None = None,
                show_exc_dialog: bool = True):
        if exc_tuple is None:
            tb = None
        elif isinstance(exc_tuple, TracebackType):
            # For API compatibility with other debuggers, the second variable
            # can be a traceback object.  In that case, we need to retrieve the
            # corresponding exception tuple.
            tb = exc_tuple
            exc, = (exc for exc in gc.get_referrers(tb)
                    if getattr(exc, "__traceback__", None) is tb)
            exc_tuple = type(exc), exc, tb
        else:
            tb = exc_tuple[2]

        if frame is None:
            assert tb is not None
            walk_frame = tb.tb_frame
        else:
            walk_frame = frame

        found_bottom_frame = False
        while True:
            if walk_frame is self.bottom_frame:
                found_bottom_frame = True
                break
            if walk_frame is None:
                break
            walk_frame = walk_frame.f_back

        if not found_bottom_frame and not self.post_mortem:
            # We aren't supposed to be debugging this.
            return

        self.stack, index = self.get_shortened_stack(frame, tb)

        if self.post_mortem:
            index = len(self.stack)-1

        self.set_frame_index(index)

        self.ui.call_with_ui(self.ui.interaction, exc_tuple,
                show_exc_dialog=show_exc_dialog)

    def get_stack_situation_id(self):
        return str(id(self.stack[self.curindex][0].f_code))

    @override
    def user_call(self, frame: FrameType, argument_list: None):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        if self._wait_for_mainpyfile:
            return
        if self.stop_here(frame):
            self.interaction(frame)

    @override
    def user_line(self, frame: FrameType):
        """This function is called when we stop or break at this line."""
        if self._waiting_for_mainpyfile(frame):
            return

        if self.get_break(self.canonic(frame.f_code.co_filename), frame.f_lineno):
            self.current_bp = (
                    self.canonic(frame.f_code.co_filename), frame.f_lineno)
        else:
            self.current_bp = None

        try:
            self.ui.update_breakpoints()
            self.interaction(frame)
        except Exception:
            self.ui.show_internal_exc_dlg(sys.exc_info())

    def user_return(self, frame, return_value):
        """This function is called when a return trap is set here."""
        if frame.f_code.co_name != "<module>":
            frame.f_locals["__return__"] = return_value

        if self._waiting_for_mainpyfile(frame):
            return

        if "__exception__" not in frame.f_locals:
            self.interaction(frame)

    def _waiting_for_mainpyfile(self, frame):
        if self._wait_for_mainpyfile:
            if (self.mainpyfile != self.canonic(frame.f_code.co_filename)
                    or frame.f_lineno <= 0):
                return True
            self._wait_for_mainpyfile = False
            self.bottom_frame = frame
            if self._continue_at_start:
                self._continue_at_start = False
                self.set_continue()
                return True
        return False

    def user_exception(self, frame, exc_info):
        """This function is called if an exception occurs,
        but only if we are to stop at or just below this level."""

        exc_type, exc_value, _exc_traceback = exc_info
        frame.f_locals["__exception__"] = exc_type, exc_value

        if not self._wait_for_mainpyfile:
            self.interaction(frame, exc_info)

    # {{{ entrypoints

    def _runscript(self, filename):
        # Provide separation from current __main__, which is likely
        # pudb.__main__ run.  Preserving its namespace is not important, and
        # having the script share it ensures that, e.g., pickle can find
        # types defined there:
        # https://github.com/inducer/pudb/issues/331

        import __main__
        __main__.__dict__.clear()
        __main__.__dict__.update({
            "__name__": "__main__",
            "__file__": filename,
            "__builtins__": __builtins__,
            })

        # When bdb sets tracing, a number of call and line events happens
        # BEFORE debugger even reaches user's code (and the exact sequence of
        # events depends on python version). So we take special measures to
        # avoid stopping before we reach the main script (see user_line and
        # user_call for details).
        self._wait_for_mainpyfile = True
        self.mainpyfile = self.canonic(filename)
        statement = f'exec(compile(open("{filename}").read(), "{filename}", "exec"))'

        # Set up an interrupt handler
        from pudb import set_interrupt_handler
        set_interrupt_handler()

        # Implicitly runs in the namespace of __main__.
        self.run(statement)

    def _runmodule(self, module_name):
        # This is basically stolen from the pdb._runmodule from CPython 3.8
        # https://github.com/python/cpython/blob/a1d3be4623c8ec7069bd34ccdce336be9cdeb644/Lib/pdb.py#L1530
        import runpy
        _mod_name, mod_spec, code = runpy._get_module_details(module_name)

        self.mainpyfile = self.canonic(code.co_filename)
        import __main__
        __main__.__dict__.clear()
        __main__.__dict__.update({
            "__name__": "__main__",
            "__file__": self.mainpyfile,
            "__spec__": mod_spec,
            "__builtins__": __builtins__,
            "__package__": mod_spec.parent,
            "__loader__": mod_spec.loader,
        })

        self._wait_for_mainpyfile = True

        self.run(code)

    def runstatement(self,
                statement: str,
                globals: dict[str, Any] | None = None,
                locals: Mapping[str, Any] | None = None
            ):
        try:
            return self.run(statement, globals, locals)
        except Exception:
            self.post_mortem = True
            self.interaction(None, sys.exc_info())
            raise

    @override
    def runeval(self,
                expression: str,
                globals: dict[str, Any] | None = None,
                locals: Mapping[str, Any] | None = None
            ):
        try:
            return super().runeval(expression, globals, locals)
        except Exception:
            self.post_mortem = True
            self.interaction(None, sys.exc_info())
            raise

    @override
    def runcall(self,
                func: Callable[P, ResultT],
                *args: P.args,
                **kwargs: P.kwargs
            ) -> ResultT | None:
        try:
            return super().runcall(func, *args, **kwargs)
        except Exception:
            self.post_mortem = True
            self.interaction(None, sys.exc_info())
            raise

    # }}}

# }}}


# UI stuff --------------------------------------------------------------------

from pudb.ui_tools import (
    BreakpointFrame,
    EventListener,
    SearchController,
    SelectableText,
    SignalWrap,
    StackFrame,
    UrwidSize,
    focus_widget_in_container,
    labelled_value,
    make_hotkey_markup,
)
from pudb.var_view import FrameVarInfoKeeper, VariableWidget, WatchExpression


# {{{ display setup

try:
    import curses
except ImportError:
    curses = None


from urwid.display.raw import Screen as RawScreen


try:
    from urwid.display.curses import Screen as CursesScreen
except ImportError:
    CursesScreen = None


class ThreadsafeScreenMixin:
    """A Screen subclass that doesn't crash when running from a non-main thread."""

    def signal_init(self):
        """Initialize signal handler, ignoring errors silently."""
        try:
            super().signal_init()
        except ValueError:
            pass

    def signal_restore(self):
        """Restore default signal handler, ignoring errors silently."""
        try:
            super().signal_restore()
        except ValueError:
            pass


class ThreadsafeRawScreen(ThreadsafeScreenMixin, RawScreen):
    pass


class ThreadsafeFixedSizeRawScreen(ThreadsafeScreenMixin, RawScreen):
    def __init__(self, **kwargs):
        self._term_size = kwargs.pop("term_size", None)
        super().__init__(**kwargs)

    def get_cols_rows(self):
        if self._term_size is not None:
            return self._term_size
        else:
            return 80, 24


if curses is not None:
    class ThreadsafeCursesScreen(ThreadsafeScreenMixin, RawScreen):
        pass

# }}}


# {{{ source code providers

class SourceCodeProvider(ABC):
    @abstractmethod
    def identifier(self) -> str:
        ...

    @abstractmethod
    def get_source_identifier(self) -> str | None:
        ...

    @abstractmethod
    def clear_cache(self):
        ...

    @abstractmethod
    def get_lines(self, debugger_ui: DebuggerUI) -> Sequence[SourceLine]:
        ...


class NullSourceCodeProvider(SourceCodeProvider):
    @override
    def __eq__(self, other: object):
        return type(self) is type(other)

    @override
    def identifier(self):
        return "<no source code>"

    @override
    def get_source_identifier(self):
        return None

    @override
    def clear_cache(self):
        pass

    @override
    def get_lines(self, debugger_ui: DebuggerUI):
        from pudb.source_view import SourceLine
        return [
                SourceLine(debugger_ui, "<no source code available>"),
                SourceLine(debugger_ui, ""),
                SourceLine(debugger_ui, "If this is generated code and you would "
                    "like the source code to show up here,"),
                SourceLine(debugger_ui, "add it to linecache.cache, like"),
                SourceLine(debugger_ui, ""),
                SourceLine(debugger_ui, "    import linecache"),
                SourceLine(debugger_ui, "    linecache.cache[filename] = "
                    "(size, mtime, lines, fullname)"),
                SourceLine(debugger_ui, ""),
                SourceLine(debugger_ui, "You can also set the attribute "
                    "_MODULE_SOURCE_CODE in the module in which this function"),
                SourceLine(debugger_ui, "was compiled to a string containing "
                    "the code."),
                ]


class FileSourceCodeProvider(SourceCodeProvider):
    file_name: str

    def __init__(self, debugger: Debugger, file_name: str):
        self.file_name = debugger.canonic(file_name)

    @override
    def __eq__(self, other: object):
        c_other = cast("FileSourceCodeProvider", other)
        return type(self) is type(other) and self.file_name == c_other.file_name

    @override
    def identifier(self):
        return self.file_name

    @override
    def get_source_identifier(self):
        return self.file_name

    @override
    def clear_cache(self):
        from linecache import clearcache
        clearcache()

    @override
    def get_lines(self, debugger_ui: DebuggerUI):
        from pudb.source_view import SourceLine, format_source

        if self.file_name == "<string>":
            return [SourceLine(debugger_ui, self.file_name)]

        breakpoints = debugger_ui.debugger.get_file_breaks(self.file_name)[:]
        breakpoints = [lineno for lineno in breakpoints if
            any(bp.enabled
                for bp in debugger_ui.debugger.get_breaks(self.file_name, lineno))]
        breakpoints += [i for f, i in debugger_ui.debugger.set_traces if f
            == self.file_name and debugger_ui.debugger.set_traces[f, i]]
        try:
            from linecache import getlines
            lines = getlines(self.file_name)
            return format_source(
                    debugger_ui, list(decode_lines(lines)), set(breakpoints))
        except Exception:
            from traceback import format_exception
            debugger_ui.message("Could not load source file '{}':\n\n{}".format(
                self.file_name, "".join(format_exception(*sys.exc_info()))),
                title="Source Code Load Error")
            return [SourceLine(debugger_ui,
                f"Error while loading '{self.file_name}'.")]


@final
class DirectSourceCodeProvider(SourceCodeProvider):
    def __init__(self, func_name: str, code: str):
        self.function_name = func_name
        self.code = code

    @override
    def __eq__(self, other: object):
        c_other = cast("DirectSourceCodeProvider", other)
        return (
                type(self) is type(other)
                and self.function_name == c_other.function_name
                and self.code is c_other.code)

    @override
    def identifier(self) -> str:
        return f"<source code of function {self.function_name}>"

    @override
    def get_source_identifier(self) -> str | None:
        return None

    @override
    def clear_cache(self):
        pass

    @override
    def get_lines(self, debugger_ui: DebuggerUI) -> Sequence[SourceLine]:
        from pudb.source_view import format_source

        lines = self.code.splitlines(True)
        return format_source(debugger_ui, list(decode_lines(lines)), set())

# }}}


class StoppedScreen:
    def __init__(self, screen):
        self.screen = screen

    def __enter__(self):
        self.screen.stop()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.screen.start()

    def press_key_to_return(self):
        with ConsoleSingleKeyReader() as key_reader:
            key_reader.get_single_key()


class DebuggerUI(FrameVarInfoKeeper):
    debugger: Debugger
    search_controller: SearchController
    last_module_filter: str
    source_code_provider: SourceCodeProvider | None
    source: urwid.SimpleListWalker[SourceLine]
    show_count: int
    current_line: SourceLine | None
    quit_event_loop: object

    current_exc_tuple: OptExcInfo | None  # pyright: ignore[reportUninitializedInstanceVariable]

    # {{{ constructor

    def __init__(self, dbg, stdin, stdout, term_size):
        FrameVarInfoKeeper.__init__(self)

        self.debugger = dbg

        from urwid import AttrMap

        from pudb.ui_tools import SearchController
        self.search_controller = SearchController(self)

        self.last_module_filter = ""

        # {{{ build ui

        # {{{ key bindings

        def move_up(w, size, key):
            w.keypress(size, "up")

        def move_down(w, size, key):
            w.keypress(size, "down")

        def move_left(w, size, key):
            w.keypress(size, "left")

        def move_right(w, size, key):
            w.keypress(size, "right")

        def page_up(w, size, key):
            w.keypress(size, "page up")

        def page_down(w, size, key):
            w.keypress(size, "page down")

        def move_home(w, size, key):
            w.keypress(size, "home")

        def move_end(w, size, key):
            w.keypress(size, "end")

        def add_vi_nav_keys(widget):
            widget.listen("k", move_up)
            widget.listen("j", move_down)
            widget.listen("h", move_left)
            widget.listen("l", move_right)
            widget.listen("ctrl b", page_up)
            widget.listen("ctrl f", page_down)
            widget.listen("ctrl u", page_up)
            widget.listen("ctrl d", page_down)
            widget.listen("g", move_home)
            widget.listen("G", move_end)

        def add_help_keys(widget, helpfunc):
            widget.listen("f1", helpfunc)
            widget.listen("?", helpfunc)

        # }}}

        # {{{ left/source column

        self.source = urwid.SimpleListWalker([])
        self.source_list = urwid.ListBox(self.source)
        self.source_sigwrap = SignalWrap(self.source_list)
        self.source_attr = urwid.AttrMap(self.source_sigwrap, "source")
        self.source_hscroll_start = 0

        self.cmdline_contents = urwid.SimpleFocusListWalker([])
        self.cmdline_list = urwid.ListBox(self.cmdline_contents)
        import urwid_readline
        self.cmdline_edit = urwid_readline.ReadlineEdit([
            ("command line prompt", ">>> ")
            ])
        cmdline_edit_attr = urwid.AttrMap(self.cmdline_edit, "command line edit")
        self.cmdline_edit_sigwrap = SignalWrap(
                cmdline_edit_attr, is_preemptive=True)

        def clear_cmdline_history(btn):
            del self.cmdline_contents[:]
            # clear the command input text too,
            # but save it to be retrieved on cmdline_history_prev()
            self.cmdline_history_position = -1
            cmdline_history_browse(1)

        def initialize_cmdline_history(path):
            dq = partial(deque, maxlen=5000)
            try:
                # Load global history if present
                with open(path) as histfile:
                    return dq(histfile.read().splitlines())
            except FileNotFoundError:
                return dq()

        self.cmdline_history_path = os.path.join(get_save_config_path(),
                                                 "internal-cmdline-history.txt")

        self.cmdline_history = initialize_cmdline_history(self.cmdline_history_path)
        self.cmdline_saved_edit_text = ""
        self.cmdline_history_position = -1

        self.cmdline_edit_bar = urwid.Columns([
                self.cmdline_edit_sigwrap,
                (urwid.FIXED, 10, AttrMap(
                    urwid.Button("Clear", clear_cmdline_history),
                    "command line clear button", "command line focused button"))
                ])

        self.cmdline_pile = urwid.Pile([
            (urwid.FLOW, urwid.Text(
                f"Command line: [{CONFIG['hotkeys_toggle_cmdline_focus']}]")),
            (urwid.WEIGHT, 1, urwid.AttrMap(
                self.cmdline_list, "command line output")),
            (urwid.FLOW, self.cmdline_edit_bar),
            ])
        self.cmdline_sigwrap = SignalWrap(
                urwid.AttrMap(self.cmdline_pile, None, "focused sidebar")
                )
        self.cmdline_on = not CONFIG["hide_cmdline_win"]
        self.cmdline_weight = float(CONFIG.get("cmdline_height", 1))
        self.lhs_col = urwid.Pile([
            (urwid.WEIGHT, 5, self.source_attr),
            (urwid.WEIGHT, self.cmdline_weight if self.cmdline_on else 0,
                self.cmdline_sigwrap),
            ])

        # }}}

        # {{{ right column

        self.locals = urwid.SimpleListWalker([])
        self.var_list = SignalWrap(
                urwid.ListBox(self.locals))

        self.stack_walker = urwid.SimpleListWalker([])
        self.stack_list = SignalWrap(
                urwid.ListBox(self.stack_walker))

        self.bp_walker = urwid.SimpleListWalker([])
        self.bp_list = SignalWrap(
                urwid.ListBox(self.bp_walker))

        self.rhs_col = urwid.Pile([
            (urwid.WEIGHT, float(CONFIG["variables_weight"]), AttrMap(urwid.Pile([
                (urwid.FLOW, urwid.Text(make_hotkey_markup("_Variables:"))),
                AttrMap(self.var_list, "variables"),
                ]), None, "focused sidebar"),),
            (urwid.WEIGHT, float(CONFIG["stack_weight"]), AttrMap(urwid.Pile([
                (urwid.FLOW, urwid.Text(make_hotkey_markup("_Stack:"))),
                AttrMap(self.stack_list, "stack"),
                ]), None, "focused sidebar"),),
            (urwid.WEIGHT, float(CONFIG["breakpoints_weight"]), AttrMap(urwid.Pile([
                (urwid.FLOW, urwid.Text(make_hotkey_markup("_Breakpoints:"))),
                AttrMap(self.bp_list, "breakpoint"),
                ]), None, "focused sidebar"),),
            ])
        self.rhs_col_sigwrap = SignalWrap(self.rhs_col)

        def helpside(w, size, key):
            help(HELP_HEADER + HELP_SIDE + HELP_MAIN + HELP_LICENSE)

        add_vi_nav_keys(self.rhs_col_sigwrap)
        add_help_keys(self.rhs_col_sigwrap, helpside)

        # }}}

        self.columns = urwid.Columns(
                    [
                        (urwid.WEIGHT, 1, self.lhs_col),
                        (urwid.WEIGHT, float(CONFIG["sidebar_width"]),
                            self.rhs_col_sigwrap),
                        ],
                    dividechars=1)

        self.caption = urwid.Text("")
        header = urwid.AttrMap(self.caption, "header")
        self.top = SignalWrap(urwid.Frame(
            urwid.AttrMap(self.columns, "background"),
            header))

        # }}}

        def change_rhs_box(name, index, direction, w, size, key):
            from pudb.settings import save_config

            weight = self.rhs_col.contents[index][1][1]

            if direction < 0:
                if weight > 1/5:
                    weight /= 1.25
            else:
                if weight < 5:
                    weight *= 1.25

            CONFIG[name+"_weight"] = weight
            save_config(CONFIG)
            self.rhs_col.contents[index] = (
                self.rhs_col.contents[index][0],
                (urwid.WEIGHT, weight))
            self.rhs_col._invalidate()

        # {{{ variables listeners

        def get_inspect_info(id_path, read_only=False):
            return (self.get_frame_var_info(read_only)
                    .get_inspect_info(id_path, read_only))

        def collapse_current(var, pos, iinfo):
            if iinfo.show_detail:
                # collapse current variable
                iinfo.show_detail = False
            else:
                # collapse parent/container variable
                if var.parent is not None:
                    p_iinfo = get_inspect_info(var.parent.id_path)
                    p_iinfo.show_detail = False
                    return self.locals.index(var.parent)
            return None

        def change_var_state(w, size, key):
            try:
                pos = self.var_list._w.focus_position
            except IndexError:
                return

            var = cast("VariableWidget | None", self.var_list._w.focus)  # pyright: ignore[reportPrivateUsage]
            if var is None:
                return

            iinfo = get_inspect_info(var.id_path)
            focus_index = None

            if key == "enter" or key == "\\" or key == " ":
                iinfo.show_detail = not iinfo.show_detail
            elif key == "h":
                focus_index = collapse_current(var, pos, iinfo)
            elif key == "l":
                iinfo.show_detail = True
            elif key == "d":
                iinfo.display_type = "default"
            elif key == "t":
                iinfo.display_type = "type"
            elif key == "r":
                iinfo.display_type = "repr"
            elif key == "s":
                iinfo.display_type = "str"
            elif key == "i":
                iinfo.display_type = "id"
            elif key == "c":
                iinfo.display_type = CONFIG["custom_stringifier"]
            elif key == "H":
                iinfo.highlighted = not iinfo.highlighted
            elif key == "@":
                iinfo.repeated_at_top = not iinfo.repeated_at_top
            elif key == "*":
                levels = ["public", "private", "all", "public"]
                iinfo.access_level = levels[levels.index(iinfo.access_level)+1]
            elif key == "w":
                iinfo.wrap = not iinfo.wrap
            elif key == "m":
                iinfo.show_methods = not iinfo.show_methods
            elif key == "delete":
                fvi = self.get_frame_var_info(read_only=False)
                for i, watch_expr in enumerate(fvi.watches):
                    if watch_expr is var.watch_expr:
                        del fvi.watches[i]
                        break

            self.update_var_view(focus_index=focus_index)

        def edit_inspector_detail(w, size, key):
            var = cast("VariableWidget | None", self.var_list._w.focus)  # pyright: ignore[reportPrivateUsage]

            if var is None:
                return

            fvi = self.get_frame_var_info(read_only=False)
            iinfo = fvi.get_inspect_info(var.id_path, read_only=False)

            buttons = [
                ("OK", True),
                ("Cancel", False),
                ]

            if var.watch_expr is not None:
                watch_edit = urwid.Edit([
                    ("label", "Watch expression: ")
                    ], var.watch_expr.expression)
                id_segment = [
                        urwid.AttrMap(watch_edit, "input", "focused input"),
                        urwid.Text(""),
                        ]

                buttons.extend([None, ("Delete", "del")])

                title = "Watch Expression Options"
            else:
                id_segment = [
                        labelled_value("Identifier Path: ", var.id_path),
                        urwid.Text(""),
                        ]

                title = "Variable Inspection Options"

            rb_grp_show = []
            rb_show_default = urwid.RadioButton(rb_grp_show, "Default",
                    iinfo.display_type == "default")
            rb_show_type = urwid.RadioButton(rb_grp_show, "Show type()",
                    iinfo.display_type == "type")
            rb_show_repr = urwid.RadioButton(rb_grp_show, "Show repr()",
                    iinfo.display_type == "repr")
            rb_show_str = urwid.RadioButton(rb_grp_show, "Show str()",
                    iinfo.display_type == "str")
            rb_show_id = urwid.RadioButton(rb_grp_show, "Show id()",
                    iinfo.display_type == "id")
            rb_show_custom = urwid.RadioButton(
                    rb_grp_show, "Show custom (set in prefs)",
                    iinfo.display_type == CONFIG["custom_stringifier"])

            rb_grp_access = []
            rb_access_public = urwid.RadioButton(rb_grp_access, "Public members",
                    iinfo.access_level == "public")
            rb_access_private = urwid.RadioButton(
                    rb_grp_access, "Public and private members",
                    iinfo.access_level == "private")
            rb_access_all = urwid.RadioButton(
                    rb_grp_access, "All members (including __dunder__)",
                    iinfo.access_level == "all")

            wrap_checkbox = urwid.CheckBox("Line Wrap", iinfo.wrap)
            expanded_checkbox = urwid.CheckBox("Expanded", iinfo.show_detail)
            highlighted_checkbox = urwid.CheckBox("Highlighted", iinfo.highlighted)
            repeated_at_top_checkbox = urwid.CheckBox(
                    "Repeated at top", iinfo.repeated_at_top)
            show_methods_checkbox = urwid.CheckBox(
                    "Show methods", iinfo.show_methods)

            lb = urwid.ListBox(urwid.SimpleListWalker(
                id_segment
                + rb_grp_show + [urwid.Text("")]
                + rb_grp_access + [urwid.Text("")]
                + [
                    wrap_checkbox,
                    expanded_checkbox,
                    highlighted_checkbox,
                    repeated_at_top_checkbox,
                    show_methods_checkbox,
                ]))

            result = self.dialog(lb, buttons, title=title)

            if result is True:
                iinfo.show_detail = expanded_checkbox.get_state()
                iinfo.wrap = wrap_checkbox.get_state()
                iinfo.highlighted = highlighted_checkbox.get_state()
                iinfo.repeated_at_top = repeated_at_top_checkbox.get_state()
                iinfo.show_methods = show_methods_checkbox.get_state()

                if rb_show_default.get_state():
                    iinfo.display_type = "default"
                elif rb_show_type.get_state():
                    iinfo.display_type = "type"
                elif rb_show_repr.get_state():
                    iinfo.display_type = "repr"
                elif rb_show_str.get_state():
                    iinfo.display_type = "str"
                elif rb_show_id.get_state():
                    iinfo.display_type = "id"
                elif rb_show_custom.get_state():
                    iinfo.display_type = CONFIG["custom_stringifier"]

                if rb_access_public.get_state():
                    iinfo.access_level = "public"
                elif rb_access_private.get_state():
                    iinfo.access_level = "private"
                elif rb_access_all.get_state():
                    iinfo.access_level = "all"

                if var.watch_expr is not None:
                    var.watch_expr = WatchExpression(watch_edit.get_edit_text())   # pyright: ignore[reportPossiblyUnboundVariable]

            elif result == "del":
                for i, watch_expr in enumerate(fvi.watches):
                    if watch_expr is var.watch_expr:
                        del fvi.watches[i]
                        break

            self.update_var_view()

        def insert_watch(w, size, key):
            watch_edit = urwid.Edit([
                ("label", "Watch expression: ")
                ])

            if self.dialog(
                    urwid.ListBox(urwid.SimpleListWalker([
                        urwid.AttrMap(watch_edit, "input", "focused input")
                        ])),
                    [
                        ("OK", True),
                        ("Cancel", False),
                        ], title="Add Watch Expression"):

                from pudb.var_view import WatchExpression
                we = WatchExpression(watch_edit.get_edit_text())
                fvi = self.get_frame_var_info(read_only=False)
                fvi.watches.append(we)
                self.update_var_view()

        self.var_list.listen("\\", change_var_state)
        self.var_list.listen(" ", change_var_state)
        self.var_list.listen("h", change_var_state)
        self.var_list.listen("l", change_var_state)
        self.var_list.listen("d", change_var_state)
        self.var_list.listen("t", change_var_state)
        self.var_list.listen("r", change_var_state)
        self.var_list.listen("s", change_var_state)
        self.var_list.listen("i", change_var_state)
        self.var_list.listen("c", change_var_state)
        self.var_list.listen("H", change_var_state)
        self.var_list.listen("@", change_var_state)
        self.var_list.listen("*", change_var_state)
        self.var_list.listen("w", change_var_state)
        self.var_list.listen("m", change_var_state)
        self.var_list.listen("enter", change_var_state)
        self.var_list.listen("e", edit_inspector_detail)
        self.var_list.listen("n", insert_watch)
        self.var_list.listen("insert", insert_watch)
        self.var_list.listen("delete", change_var_state)

        self.var_list.listen("[", partial(change_rhs_box, "variables", 0, -1))
        self.var_list.listen("]", partial(change_rhs_box, "variables", 0, 1))

        # }}}

        # {{{ stack listeners

        def examine_frame(w, size, key):
            pos = self.stack_list._w.focus_position
            self.debugger.set_frame_index(self.translate_ui_stack_index(pos))

        self.stack_list.listen("enter", examine_frame)

        def open_file_editor(file_name, line_number):
            file_changed = False

            try:
                original_modification_time = os.path.getmtime(file_name)
                with StoppedScreen(self.screen):
                    filename_edited = self.debugger.open_file_to_edit(file_name,
                                                                      line_number)
                new_modification_time = os.path.getmtime(file_name)
                file_changed = new_modification_time - original_modification_time > 0
            except Exception:
                from traceback import format_exception
                self.message("Exception happened when trying to edit the file:"
                             "\n\n{}".format("".join(format_exception(*sys.exc_info()))),
                    title="File Edit Error")
                return

            if file_changed:
                self.message("File is changed, but the execution is continued with"
                             " the 'old' codebase.\n"
                             f"Changed file: {filename_edited}\n\n"
                             "Please quit and restart to see changes",
                             title="File is changed")

        def open_editor_on_stack_frame(w, size, key):
            pos = self.stack_list._w.focus_position
            index = self.translate_ui_stack_index(pos)

            curframe, line_number = self.debugger.stack[index]
            file_name = curframe.f_code.co_filename

            open_file_editor(file_name, line_number)

        self.stack_list.listen("ctrl e", open_editor_on_stack_frame)

        def move_stack_top(w, size, key):
            self.debugger.set_frame_index(len(self.debugger.stack)-1)

        def move_stack_up(w, size, key):
            self.debugger.move_up_frame()

        def move_stack_down(w, size, key):
            self.debugger.move_down_frame()

        self.stack_list.listen("H", move_stack_top)
        self.stack_list.listen("u", move_stack_up)
        self.stack_list.listen("d", move_stack_down)

        self.stack_list.listen("[", partial(change_rhs_box, "stack", 1, -1))
        self.stack_list.listen("]", partial(change_rhs_box, "stack", 1, 1))

        # }}}

        # {{{ breakpoint listeners

        def set_breakpoint_source(bp: bdb.Breakpoint):
            bp_source_identifier = \
                    self.source_code_provider.get_source_identifier()
            if (bp.file
                    and bp_source_identifier == bp.file
                    and bp.line-1 < len(self.source)):
                self.source[bp.line-1].set_breakpoint(bp.enabled)

        def save_breakpoints(w, size, key):
            self.debugger.save_breakpoints()

        def handle_delete_breakpoint(w, size, key):
            bp_list = self._get_bp_list()
            if bp_list:
                pos = self.bp_list._w.focus_position
                bp = bp_list[pos]
                delete_breakpoint(bp)

        def delete_breakpoint(bp):
            err = self.debugger.clear_break(bp.file, bp.line)
            if err:
                self.message("Error clearing breakpoint:\n" + err)
            else:
                bp.enabled = False
                self.update_breakpoints()
                set_breakpoint_source(bp)

        def enable_disable_breakpoint(w, size, key):
            pos = self.bp_list._w.focus_position
            bp_entry = self.bp_list._w.focus
            if bp_entry is None:
                return
            bp = self._get_bp_list()[pos]
            bp.enabled = not bp.enabled
            self.update_breakpoints()
            set_breakpoint_source(bp)

        def examine_breakpoint(w, size, key):
            pos = self.bp_list._w.focus_position
            bp_entry = self.bp_list._w.focus

            if bp_entry is None:
                return

            bp = self._get_bp_list()[pos]

            if bp.cond is None:
                cond = ""
            else:
                cond = str(bp.cond)

            enabled_checkbox = urwid.CheckBox(
                    "Enabled", bp.enabled)
            cond_edit = urwid.Edit([
                ("label", "Condition:               ")
                ], cond)
            ign_count_edit = urwid.IntEdit([
                ("label", "Ignore the next N times: ")
                ], bp.ignore)

            lb = urwid.ListBox(urwid.SimpleListWalker([
                labelled_value("File: ", bp.file),
                labelled_value("Line: ", bp.line),
                labelled_value("Hits: ", bp.hits),
                urwid.Text(""),
                enabled_checkbox,
                urwid.AttrMap(cond_edit, "input", "focused input"),
                urwid.AttrMap(ign_count_edit, "input", "focused input"),
                ]))

            result = self.dialog(lb, [
                ("OK", True),
                ("Cancel", False),
                None,
                ("Delete", "del"),
                ("Location", "loc"),
                ], title="Edit Breakpoint")

            if result is True:
                bp.enabled = enabled_checkbox.get_state()
                bp.ignore = int(ign_count_edit.value())
                cond = cond_edit.get_edit_text()
                if cond:
                    bp.cond = cond
                else:
                    bp.cond = None
            elif result == "loc":
                self.show_line(bp.line,
                        FileSourceCodeProvider(self.debugger, bp.file))
                self.columns.focus_position = 0
            elif result == "del":
                delete_breakpoint(bp)

            self.update_breakpoints()
            set_breakpoint_source(bp)

        def show_breakpoint(w, size, key):
            pos = self.bp_list._w.focus_position
            bp_entry = self.bp_list._w.focus

            if bp_entry is not None:
                bp = self._get_bp_list()[pos]
                self.show_line(bp.line,
                        FileSourceCodeProvider(self.debugger, bp.file))
                self.columns.focus_position = 0

        self.bp_list.listen("enter", show_breakpoint)
        self.bp_list.listen("d", handle_delete_breakpoint)
        self.bp_list.listen("s", save_breakpoints)
        self.bp_list.listen("e", examine_breakpoint)
        self.bp_list.listen("b", enable_disable_breakpoint)
        self.bp_list.listen("H", move_stack_top)

        self.bp_list.listen("[", partial(change_rhs_box, "breakpoints", 2, -1))
        self.bp_list.listen("]", partial(change_rhs_box, "breakpoints", 2, 1))

        # }}}

        # {{{ source listeners

        def end():
            self.debugger.save_breakpoints()
            self.quit_event_loop = True

        def next_line(_w: urwid.Widget, _size: UrwidSize, _key: str):
            if self.debugger.post_mortem:
                self.message("Post-mortem mode: Can't modify state.")
            else:
                self.debugger.set_next(self.debugger.curframe)
                end()

        def step(w, size, key):
            if self.debugger.post_mortem:
                self.message("Post-mortem mode: Can't modify state.")
            else:
                self.debugger.set_step()
                end()

        def finish(w, size, key):
            if self.debugger.post_mortem:
                self.message("Post-mortem mode: Can't modify state.")
            else:
                self.debugger.set_return(self.debugger.curframe)
                end()

        def cont(w, size, key):
            if self.debugger.post_mortem:
                self.message("Post-mortem mode: Can't modify state.")
            else:
                self.debugger.set_continue()
                end()

        def run_to_cursor(w, size, key):
            if self.debugger.post_mortem:
                self.message("Post-mortem mode: Can't modify state.")
            else:
                pos = self.source.focus
                lineno = pos+1

                bp_source_identifier = \
                        self.source_code_provider.get_source_identifier()

                if bp_source_identifier is None:
                    self.message(
                        "Cannot currently set a breakpoint here--"
                        "source code does not correspond to a file location. "
                        "(perhaps this is generated code)")
                    return

                from pudb.lowlevel import get_breakpoint_invalid_reason
                invalid_reason = get_breakpoint_invalid_reason(
                        bp_source_identifier, lineno)

                if invalid_reason is not None:
                    self.message(
                        "Cannot run to the line you indicated, "
                        "for the following reason:\n\n"
                        + invalid_reason)
                else:
                    err = self.debugger.set_break(
                            bp_source_identifier, pos+1, temporary=True)
                    if err:
                        self.message("Error dealing with breakpoint:\n" + err)

                    self.debugger.set_continue()
                    end()

        def jump_to_cursor(w, size, key):
            if self.debugger.post_mortem:
                self.message("Post-mortem mode: Can't modify state.")
            else:
                pos = self.source.focus
                lineno = pos+1

                bp_source_identifier = \
                        self.source_code_provider.get_source_identifier()

                if bp_source_identifier is None:
                    self.message(
                        "Cannot jump here--"
                        "source code does not correspond to a file location. "
                        "(perhaps this is generated code)")
                    return

                from pudb.lowlevel import get_breakpoint_invalid_reason
                invalid_reason = get_breakpoint_invalid_reason(
                        bp_source_identifier, lineno)

                if invalid_reason is not None:
                    self.message(
                        "Cannot jump to the line you indicated, "
                        "for the following reason:\n\n"
                        + invalid_reason)
                else:
                    try:
                        self.debugger.set_jump(
                            self.debugger.curframe, lineno)
                        self.debugger.stack[self.debugger.curindex] = \
                            self.debugger.stack[self.debugger.curindex][0], lineno
                        self.debugger.set_step()
                    except ValueError as e:
                        self.message(f"""\
Error with jump. Note that jumping only works on the topmost stack frame.
(The error was: {e.args[0]})""")

                    # Update UI. end() will run past the line
                    assert self.source_code_provider is not None
                    self.set_current_line(lineno, self.source_code_provider)
                    self.update_stack()

        def go_to_line(w, size, key):
            line = self.source.focus

            lineno_edit = urwid.IntEdit([
                ("label", "Go to Line   :")
                ], None)

            if self.dialog(
                    urwid.ListBox(urwid.SimpleListWalker([
                        labelled_value("File :",
                            self.source_code_provider.identifier()),
                        labelled_value("Current Line :", line+1),
                        urwid.AttrMap(lineno_edit, "input", "focused input")
                        ])),
                    [
                        ("OK", True),
                        ("Cancel", False),
                        ], title="Go to Line Number"):

                value = lineno_edit.value()
                if value:
                    lineno = min(max(0, int(value)-1), len(self.source)-1)
                    self.source_list.focus_position = lineno

        def scroll_left(w, size, key):
            self.source_hscroll_start = max(
                    0,
                    self.source_hscroll_start - 4)
            for sl in self.source:
                sl._invalidate()

        def scroll_right(w, size, key):
            self.source_hscroll_start += 4
            for sl in self.source:
                sl._invalidate()

        def search(w, size, key):
            self.search_controller.open_search_ui()

        def search_next(w, size, key):
            self.search_controller.perform_search(dir=1, update_search_start=True)

        def search_previous(w, size, key):
            self.search_controller.perform_search(dir=-1, update_search_start=True)

        def toggle_breakpoint(w, size, key):
            bp_source_identifier = \
                    self.source_code_provider.get_source_identifier()

            if bp_source_identifier:
                pos = self.source_list.focus_position
                sline = self.source[pos]
                lineno = pos+1

                existing_breaks = self.debugger.get_breaks(
                        bp_source_identifier, lineno)
                if existing_breaks:
                    err = None
                    for bp in existing_breaks:
                        if not bp.enabled:
                            bp.enable()
                            sline.set_breakpoint(True)
                            # Unsure about this. Are multiple breakpoints even
                            # possible?
                            break
                    else:
                        err = self.debugger.clear_break(bp_source_identifier, lineno)
                        sline.set_breakpoint(False)
                else:
                    file_lineno = (bp_source_identifier, lineno)
                    if file_lineno in self.debugger.set_traces:
                        self.debugger.set_traces[file_lineno] = \
                                not self.debugger.set_traces[file_lineno]
                        sline.set_breakpoint(self.debugger.set_traces[file_lineno])
                        return

                    from pudb.lowlevel import get_breakpoint_invalid_reason
                    invalid_reason = get_breakpoint_invalid_reason(
                            bp_source_identifier, pos+1)

                    if invalid_reason is not None:
                        do_set = not self.dialog(
                                urwid.ListBox(
                                    urwid.SimpleListWalker([
                                        urwid.Text(
                                            "The breakpoint you just set may be "
                                            "invalid, for the following reason:\n\n"
                                            + invalid_reason),
                                        ])), [
                                            ("Cancel", True),
                                            ("Set Anyway", False),
                                            ],
                                title="Possibly Invalid Breakpoint",
                                focus_buttons=True)
                    else:
                        do_set = True

                    if do_set:
                        err = self.debugger.set_break(bp_source_identifier, pos+1)
                        sline.set_breakpoint(True)
                    else:
                        err = None

                if err:
                    self.message("Error dealing with breakpoint:\n" + err)

                self.update_breakpoints()
            else:
                self.message(
                    "Cannot currently set a breakpoint here--"
                    "source code does not correspond to a file location. "
                    "(perhaps this is generated code)")

        def helpmain(w, size, key):
            help(HELP_HEADER + HELP_MAIN + HELP_SIDE + HELP_LICENSE)

        self.source_sigwrap.listen("n", next_line)
        self.source_sigwrap.listen("s", step)
        self.source_sigwrap.listen("f", finish)
        self.source_sigwrap.listen("r", finish)
        self.source_sigwrap.listen("c", cont)
        self.source_sigwrap.listen("t", run_to_cursor)
        self.source_sigwrap.listen("J", jump_to_cursor)

        self.source_sigwrap.listen("L", go_to_line)
        self.source_sigwrap.listen("/", search)
        self.source_sigwrap.listen(",", search_previous)
        self.source_sigwrap.listen(".", search_next)

        self.source_sigwrap.listen("b", toggle_breakpoint)
        self.source_sigwrap.listen("m", partial(pick_module, self))

        self.source_sigwrap.listen("H", move_stack_top)
        self.source_sigwrap.listen("u", move_stack_up)
        self.source_sigwrap.listen("d", move_stack_down)

        # left/right scrolling have to be handled specially, normal vi keys
        # don't cut it
        self.source_sigwrap.listen("h", scroll_left)
        self.source_sigwrap.listen("l", scroll_right)

        add_vi_nav_keys(self.source_sigwrap)
        add_help_keys(self.source_sigwrap, helpmain)

        # }}}

        # {{{ command line listeners

        def cmdline_get_namespace():
            curframe = self.debugger.curframe

            from pudb.shell import SetPropagatingDict
            return SetPropagatingDict(
                    [curframe.f_locals, curframe.f_globals],
                    curframe.f_locals)

        def cmdline_tab_complete(w, size, key):
            try:
                from jedi import Interpreter
            except ImportError:
                self.add_cmdline_content(
                        "Tab completion requires jedi to be installed. ",
                        "command line error")
                return

            try:
                from packaging.version import parse as LooseVersion  # noqa: N812
            except ImportError:
                from distutils.version import LooseVersion

            import jedi
            if LooseVersion(jedi.__version__) < LooseVersion("0.16.0"):
                self.add_cmdline_content(
                        "jedi 0.16.0 is required for Tab completion",
                        "command line error")

            text = self.cmdline_edit.edit_text
            pos = self.cmdline_edit.edit_pos

            chopped_text = text[:pos]
            suffix = text[pos:]

            try:
                completions = Interpreter(
                        chopped_text,
                        [cmdline_get_namespace()]).complete()
            except Exception as e:
                # Jedi sometimes produces errors. Ignore them.
                self.add_cmdline_content(
                        f"Could not tab complete (Jedi error: '{e}')",
                        "command line error")
                return

            full_completions = [i.name_with_symbols for i in completions]
            chopped_completions = [i.complete for i in completions]

            def common_prefix(a, b):
                for i, (a_i, b_i) in enumerate(zip(a, b)):
                    if a_i != b_i:
                        return a[:i]

                return a[:max(len(a), len(b))]

            common_compl_prefix = None
            for completion in chopped_completions:
                if common_compl_prefix is None:
                    common_compl_prefix = completion
                else:
                    common_compl_prefix = common_prefix(
                            common_compl_prefix, completion)

            completed_chopped_text = common_compl_prefix

            if completed_chopped_text is None:
                return

            if (
                    len(completed_chopped_text) == 0
                    and len(completions) > 1):
                self.add_cmdline_content(
                        "   ".join(full_completions),
                        "command line output")
                return

            self.cmdline_edit.edit_text = \
                    chopped_text+completed_chopped_text+suffix
            self.cmdline_edit.edit_pos = (
                    len(chopped_text)
                    + len(completed_chopped_text))

        def cmdline_append_newline(w, size, key):
            self.cmdline_edit.insert_text("\n")

        def cmdline_exec(w, size, key):
            cmd = self.cmdline_edit.get_edit_text()
            if not cmd:
                # blank command -> refuse service
                return

            self.add_cmdline_content(">>> " + cmd, "command line input")

            if not self.cmdline_history or cmd != self.cmdline_history[-1]:
                self.cmdline_history.append(cmd)

            self.cmdline_history_position = -1
            self.cmdline_saved_edit_text = ""

            prev_sys_stdin = sys.stdin
            prev_sys_stdout = sys.stdout
            prev_sys_stderr = sys.stderr

            from io import StringIO

            sys.stdin = None
            sys.stderr = sys.stdout = StringIO()
            try:
                eval(compile(cmd, "<pudb command line>", "single"),
                     cmdline_get_namespace())
            except Exception:
                tp, val, tb = sys.exc_info()

                import traceback

                tblist = traceback.extract_tb(tb)
                del tblist[:1]
                tb_lines = traceback.format_list(tblist)
                if tb_lines:
                    tb_lines.insert(0, "Traceback (most recent call last):\n")
                tb_lines[len(tb_lines):] = traceback.format_exception_only(tp, val)

                self.add_cmdline_content("".join(tb_lines), "command line error")
            else:
                self.cmdline_edit.set_edit_text("")
            finally:
                if sys.stdout.getvalue():
                    self.add_cmdline_content(sys.stdout.getvalue(),
                                             "command line output")

                sys.stdin = prev_sys_stdin
                sys.stdout = prev_sys_stdout
                sys.stderr = prev_sys_stderr

        def cmdline_history_browse(direction):
            # Browsing the command line history can be illustrated by moving up/down
            # in the following table (no wrap-around).
            # The first column shows what is written in the command input text field,
            # the second one the corresponding value of self.cmdline_history_position
            # The actual index into the history list is given by the last column.
            #                             | history  |   history
            #      command line text      | position | list index
            # ----------------------------|----------|-----------
            # oldest_command              |    2     |     0
            # medium_command              |    1     |     1
            # recent_command              |    0     |     2
            # <current / saved edit text> |   -1     |
            #     <edit text cleared>     |   -1     |
            def pos_text(pos, text):
                if pos == -1:
                    if text:
                        # currently editing a command, save it to return to it later
                        self.cmdline_saved_edit_text = text
                    if direction > 0:
                        # clear command to be able to write a different one
                        return -1, ""
                    if direction < 0 and not text and self.cmdline_saved_edit_text:
                        # return to last saved command
                        return -1, self.cmdline_saved_edit_text

                max_hist_index = len(self.cmdline_history) - 1
                pos = max(-1, min(pos - direction, max_hist_index))

                if pos == -1:
                    return -1, self.cmdline_saved_edit_text
                return pos, self.cmdline_history[max_hist_index - pos]

            self.cmdline_history_position, self.cmdline_edit.edit_text = pos_text(
                self.cmdline_history_position, self.cmdline_edit.edit_text)
            self.cmdline_edit.edit_pos = len(self.cmdline_edit.edit_text)

        def cmdline_history_prev(w, size, key):
            cmdline_history_browse(-1)

        def cmdline_history_next(w, size, key):
            cmdline_history_browse(1)

        def toggle_cmdline_focus(w, size, key):
            focus_widget_in_container(self.columns, self.lhs_col)
            if self.lhs_col.focus is self.cmdline_sigwrap:
                if CONFIG["hide_cmdline_win"]:
                    self.set_cmdline_state(False)
                focus_widget_in_container(
                        self.lhs_col,
                        self.search_controller.search_AttrMap
                        if self.search_controller.search_box else
                        self.source_attr)
            else:
                if CONFIG["hide_cmdline_win"]:
                    self.set_cmdline_state(True)
                focus_widget_in_container(self.cmdline_pile, self.cmdline_edit_bar)
                focus_widget_in_container(self.lhs_col, self.cmdline_sigwrap)

        self.cmdline_edit_sigwrap.listen("tab", cmdline_tab_complete)
        self.cmdline_edit_sigwrap.listen("ctrl v", cmdline_append_newline)
        self.cmdline_edit_sigwrap.listen("enter", cmdline_exec)
        self.cmdline_edit_sigwrap.listen("down", cmdline_history_next)
        self.cmdline_edit_sigwrap.listen("up", cmdline_history_prev)
        self.cmdline_edit_sigwrap.listen("ctrl n", cmdline_history_next)
        self.cmdline_edit_sigwrap.listen("ctrl p", cmdline_history_prev)
        self.cmdline_edit_sigwrap.listen("esc", toggle_cmdline_focus)

        self.top.listen(CONFIG["hotkeys_toggle_cmdline_focus"], toggle_cmdline_focus)

        # {{{ command line sizing
        def set_cmdline_default_size(weight: float):
            from pudb.settings import save_config

            self.cmdline_weight = weight
            CONFIG["cmdline_height"] = weight
            save_config(CONFIG)
            self.set_cmdline_size()

        def max_cmdline(w, size, key):
            set_cmdline_default_size(5)

        def min_cmdline(w, size, key):
            set_cmdline_default_size(1/2)

        def grow_cmdline(w, size, key):
            weight = self.cmdline_weight

            if weight < 5:
                weight *= 1.25
                set_cmdline_default_size(weight)

        def shrink_cmdline(w, size, key):
            weight = self.cmdline_weight

            if weight > 1/2:
                weight /= 1.25
                set_cmdline_default_size(weight)

        def cmdline_results_scroll(w, size, key):
            size = self.cmdline_pile.get_item_size(size, 1, True)
            self.cmdline_list.keypress(size, key.lstrip("shift "))

        self.cmdline_sigwrap.listen("=", max_cmdline)
        self.cmdline_sigwrap.listen("+", grow_cmdline)
        self.cmdline_sigwrap.listen("_", min_cmdline)
        self.cmdline_sigwrap.listen("-", shrink_cmdline)
        for key in ("page up", "page down"):
            self.cmdline_sigwrap.listen("shift " + key, cmdline_results_scroll)

        # }}}

        # }}}

        # {{{ sidebar sizing

        def _set_sidebar_weight(weight: float) -> None:
            from pudb.settings import save_config

            CONFIG["sidebar_width"] = weight
            save_config(CONFIG)

            self.columns.contents[1] = (
                    self.columns.contents[1][0],
                    self.columns.options("weight", weight))

        def max_sidebar(w, size, key):
            _set_sidebar_weight(5)

        def min_sidebar(w, size, key):
            _set_sidebar_weight(1/5)

        def grow_sidebar(w, size, key):
            _widget, (_weight_literal, weight, _flag) = self.columns.contents[1]
            assert weight is not None

            if weight < 5:
                weight *= 1.25
                _set_sidebar_weight(weight)

        def shrink_sidebar(w, size, key):
            _widget, (_weight_literal, weight, _flag) = self.columns.contents[1]
            assert weight is not None

            if weight > 1/5:
                weight /= 1.25
                _set_sidebar_weight(weight)

        self.rhs_col_sigwrap.listen("=", max_sidebar)
        self.rhs_col_sigwrap.listen("+", grow_sidebar)
        self.rhs_col_sigwrap.listen("_", min_sidebar)
        self.rhs_col_sigwrap.listen("-", shrink_sidebar)

        # }}}

        # {{{ top-level listeners

        def show_output(w, size, key):
            with StoppedScreen(self.screen) as s:
                s.press_key_to_return()

        def reload_breakpoints_and_redisplay():
            reload_breakpoints()
            curr_line = self.current_line
            assert self.source_code_provider
            self.set_source_code_provider(self.source_code_provider,
                                          force_update=True)
            if curr_line is not None:
                self.current_line = self.source[int(curr_line.line_nr)-1]
                self.current_line.set_current(True)

        def reload_breakpoints():
            self.debugger.clear_all_breaks()
            from pudb.settings import load_breakpoints
            for bpoint_descr in load_breakpoints():
                dbg.set_break(*bpoint_descr)
            self.update_breakpoints()

        def show_traceback(w, size, key):
            if self.current_exc_tuple is not None:
                from traceback import format_exception

                result = self.dialog(
                        urwid.ListBox(urwid.SimpleListWalker([urwid.Text(
                            "".join(format_exception(*self.current_exc_tuple)))])),
                        [
                            ("Close", "close"),
                            ("Location", "location")
                            ],
                        title="Exception Viewer",
                        focus_buttons=True,
                        bind_enter_esc=False)

                if result == "location":
                    self.debugger.set_frame_index(len(self.debugger.stack)-1)

            else:
                self.message("No exception available.")

        def run_external_cmdline(w, size, key):
            with StoppedScreen(self.screen):
                curframe = self.debugger.curframe

                import pudb.shell as shell
                if CONFIG["shell"] == "ipython" and shell.have_ipython():
                    runner = shell.run_ipython_shell
                elif CONFIG["shell"] == "ipython_kernel" and shell.have_ipython():
                    runner = shell.run_ipython_kernel
                elif CONFIG["shell"] == "bpython" and shell.HAVE_BPYTHON:
                    runner = shell.run_bpython_shell
                elif CONFIG["shell"] == "ptpython" and shell.HAVE_PTPYTHON:
                    runner = shell.run_ptpython_shell
                elif CONFIG["shell"] == "ptipython" and shell.HAVE_PTIPYTHON:
                    runner = shell.run_ptipython_shell
                elif CONFIG["shell"] == "classic":
                    runner = shell.run_classic_shell
                else:
                    def fallback(error_message):
                        fallback_message = "Falling back to classic shell."
                        message = f"{error_message} {fallback_message}"
                        ui_log.error(message)
                        return partial(shell.run_classic_shell, message=message)

                    try:
                        if not shell.custom_shell_dict:  # Only execfile once
                            from os.path import expanduser, expandvars
                            cshell_fname = expanduser(expandvars(CONFIG["shell"]))
                            with open(cshell_fname) as inf:
                                exec(compile(inf.read(), cshell_fname, "exec"),
                                        shell.custom_shell_dict,
                                        shell.custom_shell_dict)
                    except FileNotFoundError:
                        runner = fallback(
                            "Unable to locate custom shell file {!r}."
                            .format(CONFIG["shell"])
                        )
                    except Exception:
                        runner = fallback("Error when importing custom shell.")
                    else:
                        if "pudb_shell" not in shell.custom_shell_dict:
                            runner = fallback(
                                "{} does not contain a function named pudb_shell at "
                                "the module level.".format(CONFIG["shell"])
                            )
                        else:
                            runner = shell.custom_shell_dict["pudb_shell"]

                runner(curframe.f_globals, curframe.f_locals)

            self.update_var_view()

        def run_cmdline(w, size, key):
            if CONFIG["shell"] == "internal":
                return toggle_cmdline_focus(w, size, key)
            else:
                return run_external_cmdline(w, size, key)

        def focus_code(w, size, key):
            focus_widget_in_container(self.columns, self.lhs_col)
            focus_widget_in_container(self.lhs_col, self.source_attr)

        class RHColumnFocuser:
            def __init__(self, idx):
                self.idx = idx

            def __call__(subself, w, size, key):  # noqa # pylint: disable=no-self-argument
                focus_widget_in_container(self.columns, self.rhs_col_sigwrap)
                self.rhs_col.focus_position = subself.idx

        def quit(w, size, key):
            with open(self.cmdline_history_path, "w") as history:
                history.write("\n".join(self.cmdline_history))
            self.debugger.set_quit()
            end()

        def do_edit_config(w, size, key):
            self.run_edit_config()

        def redraw_screen(w, size, key):
            self.screen.clear()

        def help(pages):
            self.message(pages, title="PuDB - The Python Urwid Debugger")

        def edit_current_frame(w, size, key):
            pos = self.source.focus
            source_identifier = \
                    self.source_code_provider.get_source_identifier()

            if source_identifier is None:
                self.message(
                    "Cannot edit the current file--"
                    "source code does not correspond to a file location. "
                    "(perhaps this is generated code)")
            open_file_editor(source_identifier, pos+1)

        self.top.listen("o", show_output)
        self.top.listen("ctrl r",
                        lambda w, size, key: reload_breakpoints_and_redisplay())
        self.top.listen("!", run_cmdline)
        self.top.listen("e", show_traceback)

        self.top.listen(CONFIG["hotkeys_code"], focus_code)
        self.top.listen(CONFIG["hotkeys_variables"], RHColumnFocuser(0))
        self.top.listen(CONFIG["hotkeys_stack"], RHColumnFocuser(1))
        self.top.listen(CONFIG["hotkeys_breakpoints"], RHColumnFocuser(2))

        self.top.listen("q", quit)
        self.top.listen("ctrl p", do_edit_config)
        self.top.listen("ctrl l", redraw_screen)

        self.top.listen("ctrl e", edit_current_frame)

        # }}}

        # {{{ setup

        want_curses_display = (
                CONFIG["display"] == "curses"
                or (
                    CONFIG["display"] == "auto"
                    and not (
                        os.environ.get("TERM", "").startswith("xterm")
                        or os.environ.get("TERM", "").startswith("rxvt")
                    )))

        if (want_curses_display
                and not (stdin is not None or stdout is not None)
                and CursesScreen is not None):
            self.screen = ThreadsafeCursesScreen()
        else:
            screen_kwargs = {}
            if stdin is not None:
                screen_kwargs["input"] = stdin
            if stdout is not None:
                screen_kwargs["output"] = stdout
            if term_size is not None:
                screen_kwargs["term_size"] = term_size

            if screen_kwargs:
                self.screen = ThreadsafeFixedSizeRawScreen(**screen_kwargs)
            else:
                self.screen = ThreadsafeRawScreen()

        del want_curses_display

        if curses:
            try:
                curses.setupterm()
            except Exception:
                # Something went wrong--oh well. Nobody will die if their
                # 256 color support breaks. Just carry on without it.
                # https://github.com/inducer/pudb/issues/78
                pass
            else:
                color_support = curses.tigetnum("colors")

                if color_support == 256 and isinstance(self.screen, RawScreen):
                    self.screen.set_terminal_properties(256)

        self.setup_palette(self.screen)

        self.show_count = 0
        self.source_code_provider = None

        self.current_line = None

        self.quit_event_loop = False

        # }}}

    # }}}

    # {{{ UI helpers
    def add_cmdline_content(self, s, attr):
        s = s.rstrip("\n")

        from pudb.ui_tools import SelectableText
        self.cmdline_contents.append(
                urwid.AttrMap(SelectableText(s), attr, "focused "+attr))

        # scroll to end of last entry
        self.cmdline_list.set_focus_valign("bottom")
        self.cmdline_list.set_focus(len(self.cmdline_contents) - 1,
                coming_from="above")

        # Force the commandline to be visible
        self.set_cmdline_state(True)

    def reset_cmdline_size(self):
        self.lhs_col.contents[-1] = (
                self.lhs_col.contents[-1][0],
                (urwid.WEIGHT, self.cmdline_weight if self.cmdline_on else 0))

    def set_cmdline_size(self, weight=None):
        if weight is None:
            weight = self.cmdline_weight

        self.lhs_col.contents[-1] = (
                self.lhs_col.contents[-1][0],
                (urwid.WEIGHT, weight))
        self.lhs_col._invalidate()

    def set_cmdline_state(self, state_on):
        if state_on != self.cmdline_on:
            self.cmdline_on = state_on
            self.set_cmdline_size(None if state_on else 0)

    def translate_ui_stack_index(self, index):
        # note: self-inverse

        if CONFIG["current_stack_frame"] == "top":
            return len(self.debugger.stack)-1-index
        elif CONFIG["current_stack_frame"] == "bottom":
            return index
        else:
            raise ValueError("invalid value for 'current_stack_frame' pref")

    def message(self,
                msg: str,
                title: str = "Message",
                extra_bindings: Sequence[
                    tuple[str, str | EventListener[urwid.Widget]]] | None = None,
            ):
        return self.call_with_ui(self.dialog,
                urwid.ListBox(urwid.SimpleListWalker([urwid.Text(msg)])),
                [("OK", True)], title=title, extra_bindings=extra_bindings)

    def run_edit_config(self):
        from pudb.settings import edit_config, save_config
        edit_config(self, CONFIG)
        save_config(CONFIG)

    def dialog(self,
                content: urwid.Widget,
                buttons_and_results: Sequence[tuple[str, object] | None],
                title: str | None = None,
                bind_enter_esc: bool = True,
                focus_buttons: bool = False,
                extra_bindings: Sequence[
                    tuple[str, str | EventListener[urwid.Widget]]] | None = None,
            ) -> object:
        if extra_bindings is None:
            extra_bindings = []

        Attr = urwid.AttrMap  # noqa

        if bind_enter_esc:
            content = SignalWrap(content)

            def enter(w, size, key):
                self.quit_event_loop = (True,)

            def esc(w, size, key):
                self.quit_event_loop = (False,)

            content.listen("enter", enter)
            content.listen("esc", esc)

        # Results get wrapped in tuples because the main loop considers the truthiness
        # of the value. Once wrapped in a tuple, (False,) is still truthy.
        button_widgets: list[urwid.Widget] = []
        for btn_descr in buttons_and_results:
            if btn_descr is None:
                button_widgets.append(urwid.Text(""))
            else:
                btn_text, btn_result = btn_descr
                button_widgets.append(
                        Attr(urwid.Button(btn_text,
                                    OnButtonEventLoopResultSetter(self, (btn_result,))),
                            "button", "focused button"))

        w = urwid.Columns([
            content,
            (urwid.FIXED, 15, urwid.ListBox(urwid.SimpleListWalker(button_widgets))),
            ], dividechars=1)

        if focus_buttons:
            w.focus_position = 1

        if title is not None:
            w = urwid.Pile([
                (urwid.FLOW, urwid.AttrMap(
                    urwid.Text(title, align="center"),
                    "dialog title")),
                (urwid.FIXED, 1, urwid.SolidFill()),
                w])

        w = SignalWrap(w)
        for key, binding in extra_bindings:
            if callable(binding):
                w.listen(key, binding)
            else:
                w.listen(key, ResultSettingEventHandler(self, (binding,)))

        w = urwid.LineBox(w)

        w = urwid.Overlay(w, self.top,
                align="center",
                valign="middle",
                width=("relative", 75),
                height=("relative", 75),
                )
        w = Attr(w, "background")

        return cast("tuple[object]", self.event_loop(w))[0]

    @staticmethod
    def setup_palette(screen):
        may_use_fancy_formats = not hasattr(urwid.escape, "_fg_attr_xterm")

        from pudb.theme import get_palette
        palette = get_palette(may_use_fancy_formats, CONFIG["theme"])
        if palette:
            screen.register_palette(palette)

    def show_exception_dialog(self, exc_tuple: OptExcInfo):
        from traceback import format_exception

        desc = (
            "The program has terminated abnormally because of an exception.\n\n"
            "A full traceback is below. You may recall this traceback at any "
            "time using the 'e' key. The debugger has entered post-mortem mode "
            "and will prevent further state changes."
        )
        tb_txt = "".join(format_exception(*exc_tuple))
        self._show_exception_dialog(
            description=desc,
            error_info=tb_txt,
            title="Program Terminated for Uncaught Exception",
            exit_loop_on_ok=True,
        )

    def show_internal_exc_dlg(self, exc_tuple: OptExcInfo):
        try:
            self._show_internal_exc_dlg(exc_tuple)
        except Exception:
            ui_log.exception("Error while showing error dialog")

    def _show_internal_exc_dlg(self, exc_tuple: OptExcInfo):
        from traceback import format_exception

        from pudb import VERSION

        desc = (
            "Pudb has encountered and safely caught an internal exception.\n\n"
            "The full traceback and some other information can be found "
            "below. Please report this information, along with details on "
            "what you were doing at the time the exception occurred, at: "
            "https://github.com/inducer/pudb/issues"
        )
        error_info = (
            "python version: {python}\n"
            "pudb version: {pudb}\n"
            "urwid version: {urwid}\n"
            "{tb}\n"
        ).format(
            python=sys.version.replace("\n", " "),
            pudb=VERSION,
            urwid=".".join(map(str, urwid.version.version)),
            tb="".join(format_exception(*exc_tuple))
        )

        self._show_exception_dialog(
            description=desc,
            error_info=error_info,
            title="Pudb Internal Exception Encountered",
        )

    def _show_exception_dialog(self,
                description: str,
                error_info: str,
                title: str,
                exit_loop_on_ok: bool = False):
        res = self.dialog(
            urwid.ListBox(urwid.SimpleListWalker([urwid.Text(
                "\n\n".join([description, error_info])
            )])),
            title=title,
            buttons_and_results=[
                ("OK", exit_loop_on_ok),
                ("Save traceback", "save"),
            ],
        )
        if res == "save":
            self._save_traceback(error_info)

    def _save_traceback(self, error_info: str):
        try:
            from os.path import exists
            filename = next(
                fname for n in count()
                for fname in ["traceback-%d.txt" % n if n else "traceback.txt"]
                if not exists(fname)
            )

            with open(filename, "w") as outf:
                outf.write(error_info)

            self.message(f"Traceback saved as {filename}.", title="Success")

        except Exception:
            from traceback import format_exception
            io_tb_txt = "".join(format_exception(*sys.exc_info()))
            self.message(
                    "An error occurred while trying to write "
                    "the traceback:\n\n" + io_tb_txt,
                    title="I/O error")
    # }}}

    # {{{ UI enter/exit

    def _show(self):
        if self.show_count == 0:
            self.screen.start()
        self.show_count += 1

    def _hide(self):
        self.show_count -= 1
        if self.show_count == 0:
            self.screen.stop()

    def call_with_ui(self,
                f: Callable[P, ResultT],
                *args: P.args,
                **kwargs: P.kwargs
            ):
        import warnings

        def myshowwarning(
                  message, category, filename, lineno, file=None, line=None
              ) -> None:
            msg = warnings.formatwarning(
                     message=message, category=category,
                     filename=filename, lineno=lineno, line=line)
            self.add_cmdline_content(msg, "command line error")

        with warnings.catch_warnings():
            warnings.resetwarnings()
            warnings.showwarning = myshowwarning

            self._show()
            try:
                return f(*args, **kwargs)
            finally:
                self._hide()

    # }}}

    # {{{ event loop

    def event_loop(self, toplevel: urwid.Widget | None = None) -> object:
        prev_quit_loop = self.quit_event_loop

        try:
            import pygments  # noqa
        except ImportError:
            if not hasattr(self, "pygments_message_shown"):
                self.pygments_message_shown = True
                self.message("Package 'pygments' not found. "
                        "Syntax highlighting disabled.")

        WELCOME_LEVEL = "e054"  # noqa
        if CONFIG["seen_welcome"] < WELCOME_LEVEL:
            CONFIG["seen_welcome"] = WELCOME_LEVEL
            from pudb import VERSION
            self.message(f"Welcome to PudB {VERSION}!\n\n"
                    "PuDB is a full-screen, console-based visual debugger for "
                    "Python.  Its goal is to provide all the niceties of modern "
                    "GUI-based debuggers in a more lightweight and "
                    "keyboard-friendly package. "
                    "PuDB allows you to debug code right where you write and test "
                    "it--in a terminal. If you've worked with the excellent "
                    "(but nowadays ancient) DOS-based Turbo Pascal or C tools, "
                    "PuDB's UI might look familiar.\n\n"
                    "If you're new here, welcome! The help screen "
                    "(invoked by hitting '?' after this message) should get you "
                    "on your way.\n"

                    "\nChanges in version 2025.1.3:\n\n"
                    "- Actually fix module picking\n"
                    "- Fix bugs introduced by typing improvements\n"

                    "\nChanges in version 2025.1.2:\n\n"
                    "- Fix module picking\n"
                    "- Work towards improved type checking coverage\n"

                    "\nChanges in version 2025.1.1:\n\n"
                    "- Fix a call to format_exception (Lumír 'Frenzy' Balhar)\n"
                    "- Fix set_trace(paused=False) (Aaron Meurer)\n"
                    "- Expose post_mortem in pudb.remote (Gabriel Pettier)\n"
                    "- Work towards improved type checking coverage\n"

                    "\nChanges in version 2025.1:\n\n"
                    "- Fix compatibility with Urwid 3\n"
                    "- Allow leaving output screen with single key press "
                    "(Gerhard Sittig)\n"

                    "\nChanges in version 2024.1.3:\n\n"
                    "- Switch to hatchling build system\n"
                    "- Fix compatibility with Python 3.13\n"
                    "- Fix startup without write permissions (Fergal Armstrong)\n"

                    "\nChanges in version 2024.1.2:\n\n"
                    "- Fix separate-terminal debugging (Matt Rixman)\n"

                    "\nChanges in version 2024.1.1:\n\n"
                    "- Fix some urwid.util deprecation warnings\n"
                    "- Redirect pudb warnings to console\n"
                    "- Catch IndexError on empty Variables state "
                    "(Michael van der Kamp)\n"

                    "\nChanges in version 2024.1:\n\n"
                    "- Control remote debugging via env vars (Max Arnold)\n"
                    "- Adapt to, depend on urwid 2.4\n"
                    "- Make compatible with Python 3.13 (Will Shanks)\n"
                    "- Use co_lines mechanism for line finding executable lines"
                    "when available\n"

                    "\nChanges in version 2023.1:\n\n"
                    "- Add nord-256 theme (Jorge Gomez, Michael van der Kamp)\n"
                    "- Reorganize themes, add light gray theme "
                    "(Michael van der Kamp)\n"
                    "- Improve command line history handling (raphTec)\n"
                    "- Implement jump command (Aaron Meurer)\n"
                    "- Drop support for Python 3.6, 3.7\n"
                    "- Improve sidebar help (kwmiebach)\n"
                    "- Bug fixes\n"

                    "\nChanges in version 2022.1.3:\n\n"
                    "- Fix finding executable lines for Python 3.11 (Lumir Balhar)\n"
                    "- Fix the midnight theme (Aaron Meurer)\n"
                    "- Add a --continue flag (Michael van der Kamp)\n"
                    "- Various fixes\n"

                    "\nChanges in version 2022.1.2:\n\n"
                    "- Various fixes\n"

                    "\nChanges in version 2022.1.1:\n\n"
                    "- Fix ptpython shell invocation with nonempty argv (gh-510)\n"
                    "- Make some key bindings configurable (Cibin Mathew)\n"
                    "- Various cleanups (Michael van der Kamp)\n"

                    "\nChanges in version 2022.1:\n\n"
                    "- Add debug_remote_on_single_rank "
                    "(PR #498 by Matthias Diener)\n"
                    "- Improve remote debugging usability\n"
                    "- Bug fixes\n"

                    "\nChanges in version 2021.2:\n\n"
                    "- Remaster themes (Michael van der Kamp)\n"
                    "- Add more internal shell shortcuts (Huy Nguyen Quang)\n"
                    "- Save internal shell history between sessions "
                    "(Diego Velazquez)\n"
                    "- Various bug fixes\n"

                    "\nChanges in version 2021.1:\n\n"
                    "- Add shortcut to edit files in source and stack view "
                    "(Gábor Vecsei)\n"
                    "- Major improvements to the variable view "
                    "(Michael van der Kamp)\n"
                    "- Better internal error reporting (Michael van der Kamp)\n"

                    "\nChanges in version 2020.1:\n\n"
                    "- Add vi keys for the sidebar (Asbjørn Apeland)\n"
                    "- Add -m command line switch (Elias Dorneles)\n"
                    "- Debug forked processes (Jonathan Striebel)\n"
                    "- Robustness and logging for internal errors "
                    "(Michael Vanderkamp)\n"
                    "- 'Reverse' remote debugging (jen6)\n"

                    "\nChanges in version 2019.2:\n\n"
                    "- Auto-hide the command line (Mark Blakeney)\n"
                    "- Improve help and add jump to breakpoint (Mark Blakeney)\n"
                    "- Drop Py2.6 support\n"
                    "- Show callable attributes in var view\n"
                    "- Allow scrolling sidebar with j/k\n"
                    "- Fix setting breakpoints in Py3.8 (Aaron Meurer)\n"

                    "\nChanges in version 2019.1:\n\n"
                    "- Allow 'space' as a key to expand variables (Enrico Troeger)\n"
                    "- Have a persistent setting on variable visibility \n"
                    "  (Enrico Troeger)\n"
                    "- Enable/partially automate opening the debugger in another \n"
                    "  terminal (Anton Barkovsky)\n"
                    "- Make sidebar scrollable with j/k (Clayton Craft)\n"
                    "- Bug fixes.\n"

                    "\nChanges in version 2018.1:\n\n"
                    "- Bug fixes.\n"

                    "\nChanges in version 2017.1.4:\n\n"
                    "- Bug fixes.\n"

                    "\nChanges in version 2017.1.3:\n\n"
                    "- Add handling of safely_stringify_for_pudb to allow custom \n"
                    "  per-type stringification.\n"
                    "- Add support for custom shells.\n"
                    "- Better support for 2-wide characters in the var view.\n"
                    "- Bug fixes.\n"

                    "\nChanges in version 2017.1.2:\n\n"
                    "- Bug fixes.\n"

                    "\nChanges in version 2017.1.1:\n\n"
                    "- IMPORTANT: 2017.1 and possibly earlier versions had a \n"
                    "  bug with exponential growth of shell history for the \n"
                    "  'classic' shell, which (among other problems) could lead\n"
                    "  to slow startup of the classic shell. Check the file\n\n"
                    "  ~/.config/pudb/shell-history\n\n"
                    "  for size (and useful content) and delete/trim as needed.\n"

                    "\nChanges in version 2017.1:\n\n"
                    "- Many, many bug fixes (thank you to all who contributed!)\n"

                    "\nChanges in version 2016.2:\n\n"
                    "- UI improvements for disabled breakpoints.\n"
                    "- Bug fixes.\n"

                    "\nChanges in version 2016.1:\n\n"
                    "- Fix module browser on Py3.\n"

                    "\nChanges in version 2015.4:\n\n"
                    "- Support for (somewhat rudimentary) remote debugging\n"
                    "  through a telnet connection.\n"
                    "- Fix debugging of generated code in Python 3.\n"

                    "\nChanges in version 2015.3:\n\n"
                    "- Disable set_trace lines from the UI (Aaron Meurer)\n"
                    "- Better control over attribute visibility (Ned Batchelder)\n"

                    "\nChanges in version 2015.2:\n\n"
                    "- ptpython support (P. Varet)\n"
                    "- Improved rxvt support (Louper Rouch)\n"
                    "- More keyboard shortcuts in the command line"
                    "(Alex Sheluchin)\n"

                    "\nChanges in version 2015.1:\n\n"
                    "- Add solarized theme (Rinat Shigapov)\n"
                    "- More keyboard shortcuts in the command line"
                    "(Alexander Corwin)\n"

                    "\nChanges in version 2014.1:\n\n"
                    "- Make prompt-on-quit optional (Mike Burr)\n"
                    "- Make tab completion in the built-in shell saner\n"
                    "- Fix handling of unicode source\n"
                    "  (reported by Morten Nielsen and Buck Golemon)\n"

                    "\nChanges in version 2013.5.1:\n\n"
                    "- Fix loading of saved breakpoint conditions "
                    "(Antoine Dechaume)\n"
                    "- Fixes for built-in command line\n"
                    "- Theme updates\n"

                    "\nChanges in version 2013.5:\n\n"
                    "- Add command line window\n"
                    "- Uses curses display driver when appropriate\n"

                    "\nChanges in version 2013.4:\n\n"
                    "- Support for debugging generated code\n"

                    "\nChanges in version 2013.3.5:\n\n"
                    "- IPython fixes (Aaron Meurer)\n"
                    "- Py2/3 configuration fixes (Somchai Smythe)\n"
                    "- PyPy fixes (Julian Berman)\n"

                    "\nChanges in version 2013.3.4:\n\n"
                    "- Don't die if curses doesn't like what stdin/out are\n"
                    "  connected to.\n"

                    "\nChanges in version 2013.3.3:\n\n"
                    "- As soon as pudb is loaded, you can break to the debugger by\n"
                    "  evaluating the expression 'pu.db', where 'pu' is a new \n"
                    "  'builtin' that pudb has rudely shoved into the interpreter.\n"

                    "\nChanges in version 2013.3.2:\n\n"
                    "- Don't attempt to do signal handling if a signal handler\n"
                    "  is already set (Fix by Buck Golemon).\n"

                    "\nChanges in version 2013.3.1:\n\n"
                    "- Don't ship {ez,distribute}_setup at all.\n"
                    "  It breaks more than it helps.\n"

                    "\nChanges in version 2013.3:\n\n"
                    "- Switch to setuptools as a setup helper.\n"

                    "\nChanges in version 2013.2:\n\n"
                    "- Even more bug fixes.\n"

                    "\nChanges in version 2013.1:\n\n"
                    "- Ctrl-C will now break to the debugger in a way that does\n"
                    "  not terminate the program\n"
                    "- Lots of bugs fixed\n"

                    "\nChanges in version 2012.3:\n\n"
                    "- Python 3 support (contributed by Brad Froehle)\n"
                    "- Better search box behavior (suggested by Ram Rachum)\n"
                    "- Made it possible to go back and examine state from "
                    "'finished' window. (suggested by Aaron Meurer)\n"

                    "\nChanges in version 2012.2.1:\n\n"
                    "- Don't touch config files during install.\n"

                    "\nChanges in version 2012.2:\n\n"
                    "- Add support for BPython as a shell.\n"
                    "- You can now run 'python -m pudb script.py' on Py 2.6+.\n"
                    "  '-m pudb.run' still works--but it's four "
                    "keystrokes longer! :)\n"

                    "\nChanges in version 2012.1:\n\n"
                    "- Work around an API change in IPython 0.12.\n"

                    "\nChanges in version 2011.3.1:\n\n"
                    "- Work-around for bug in urwid >= 1.0.\n"

                    "\nChanges in version 2011.3:\n\n"
                    "- Finer-grained string highlighting "
                    "(contributed by Aaron Meurer)\n"
                    "- Prefs tweaks, instant-apply, top-down stack "
                    "(contributed by Aaron Meurer)\n"
                    "- Size changes in sidebar boxes (contributed by Aaron Meurer)\n"
                    "- New theme 'midnight' (contributed by Aaron Meurer)\n"
                    "- Support for IPython 0.11 (contributed by Chris Farrow)\n"
                    "- Support for custom stringifiers "
                    "(contributed by Aaron Meurer)\n"
                    "- Line wrapping in variables view "
                    "(contributed by Aaron Meurer)\n"

                    "\nChanges in version 2011.2:\n\n"
                    "- Fix for post-mortem debugging (contributed by 'Sundance')\n"

                    "\nChanges in version 2011.1:\n\n"
                    "- Breakpoints saved between sessions\n"
                    "- A new 'dark vim' theme\n"
                    "(both contributed by Naveen Michaud-Agrawal)\n"

                    "\nChanges in version 0.93:\n\n"
                    "- Stored preferences (no more pesky IPython prompt!)\n"
                    "- Themes\n"
                    "- Line numbers (optional)\n")
            from pudb.settings import save_config
            save_config(CONFIG)
            self.run_edit_config()

        try:
            if toplevel is None:
                toplevel = self.top

            self.size = self.screen.get_cols_rows()

            self.quit_event_loop = False

            while not self.quit_event_loop:
                canvas = toplevel.render(self.size, focus=True)
                self.screen.draw_screen(self.size, canvas)
                keys = self.screen.get_input()

                for k in keys:  # pylint: disable=not-an-iterable
                    if k == "window resize":
                        self.size = self.screen.get_cols_rows()
                    else:
                        try:
                            toplevel.keypress(self.size, k)
                        except Exception:
                            self.show_internal_exc_dlg(sys.exc_info())

            return self.quit_event_loop
        finally:
            self.quit_event_loop = prev_quit_loop

    # }}}

    # {{{ debugger-facing interface

    def interaction(self, exc_tuple: OptExcInfo | None, show_exc_dialog: bool = True):
        self.current_exc_tuple = exc_tuple

        from pudb import VERSION
        caption = [(None,
            f"PuDB {VERSION} - ?:help  n:next  s:step into  b:breakpoint  "
            "!:python command line")]

        if self.debugger.post_mortem:
            if show_exc_dialog and exc_tuple is not None:
                self.show_exception_dialog(exc_tuple)

            caption.extend([
                (None, " "),
                ("header warning", "[POST-MORTEM MODE]")
                ])
        elif exc_tuple is not None:
            caption.extend([
                (None, " "),
                ("header warning", "[PROCESSING EXCEPTION - hit 'e' to examine]")
                ])

        self.caption.set_text(caption)
        self.event_loop()

    def set_source_code_provider(self,
                source_code_provider: SourceCodeProvider,
                force_update: bool = False):
        if self.source_code_provider != source_code_provider or force_update:
            self.source[:] = source_code_provider.get_lines(self)
            self.source_code_provider = source_code_provider
            self.current_line = None

    def show_line(self, line, source_code_provider=None):
        """Updates the UI so that a certain line is currently in view."""

        changed_file = False
        if source_code_provider is not None:
            changed_file = self.source_code_provider != source_code_provider
            self.set_source_code_provider(source_code_provider)

        line -= 1
        if line >= 0 and line < len(self.source):
            self.source_list.focus_position = line
            if changed_file:
                self.source_list.set_focus_valign("middle")

    def set_current_line(self, line: int, source_code_provider: SourceCodeProvider):
        """Updates the UI to show the line currently being executed."""

        if self.current_line is not None:
            self.current_line.set_current(False)

        self.show_line(line, source_code_provider)

        line -= 1
        if line >= 0 and line < len(self.source):
            self.current_line = self.source[line]
            self.current_line.set_current(True)

    def update_var_view(self, locals=None, globals=None, focus_index=None):
        if locals is None:
            locals = self.debugger.curframe.f_locals
        if globals is None:
            globals = self.debugger.curframe.f_globals

        from pudb.var_view import make_var_view
        self.locals[:] = make_var_view(
                self.get_frame_var_info(read_only=True),
                locals, globals)
        if focus_index is not None:
            # Have to set the focus _after_ updating the locals list, as there
            # appears to be a brief moment while resetting the list when the
            # list is empty but urwid will attempt to set the focus anyway,
            # which causes problems.
            try:
                self.var_list._w.focus_position = focus_index
            except IndexError:
                # sigh oh well we tried
                pass

    def _get_bp_list(self):
        return [bp
                for fn, bp_lst in self.debugger.get_all_breaks().items()
                for lineno in bp_lst
                for bp in self.debugger.get_breaks(fn, lineno)
                if not bp.temporary]

    def _format_fname(self, fname):
        from os.path import basename, dirname
        name = basename(fname)

        if name == "__init__.py":
            name = "..."+dirname(fname)[-10:]+"/"+name
        return name

    def update_breakpoints(self):
        self.bp_walker[:] = [
                BreakpointFrame(self.debugger.current_bp == (bp.file, bp.line),
                    self._format_fname(bp.file), bp)
                for bp in self._get_bp_list()]

    def update_stack(self):
        def make_frame_ui(i, frame_lineno):
            frame, lineno = frame_lineno

            code = frame.f_code

            class_name = None
            if code.co_argcount and code.co_varnames[0] == "self":
                try:
                    class_name = frame.f_locals["self"].__class__.__name__
                except Exception:
                    from pudb.lowlevel import ui_log
                    message = "Failed to determine class name"
                    ui_log.exception(message)
                    class_name = f"!! {message} !!"

            return StackFrame(i == self.debugger.curindex,
                    code.co_name, class_name,
                    self._format_fname(code.co_filename), lineno)

        frame_uis = [make_frame_ui(i, fl)
                for i, fl in enumerate(self.debugger.stack)]
        if CONFIG["current_stack_frame"] == "top":
            frame_uis = frame_uis[::-1]
        elif CONFIG["current_stack_frame"] == "bottom":
            pass
        else:
            raise ValueError("invalid value for 'current_stack_frame' pref")

        self.stack_walker[:] = frame_uis

    def update_cmdline_win(self):
        self.set_cmdline_state(not CONFIG["hide_cmdline_win"])

    # }}}


@dataclass(frozen=True)
class OnButtonEventLoopResultSetter:
    ui: DebuggerUI
    res: object

    def __call__(self, btn: urwid.Button):
        self.ui.quit_event_loop = self.res


@dataclass(frozen=True)
class ResultSettingEventHandler:
    ui: DebuggerUI
    res: object

    def __call__(self, w: urwid.Widget, size: UrwidSize, key: str):
        self.ui.quit_event_loop = self.res

# vim: foldmethod=marker:expandtab:softtabstop=4
