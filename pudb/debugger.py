#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import urwid
import bdb
import sys
import os

from pudb.settings import load_config, save_config
CONFIG = load_config()
save_config(CONFIG)

from pudb.py3compat import PY3, raw_input
if PY3:
    _next = "__next__"
else:
    _next = "next"

try:
    from functools import partial
except ImportError:
    def partial(func, *args, **keywords):
        def newfunc(*fargs, **fkeywords):
            newkeywords = keywords.copy()
            newkeywords.update(fkeywords)
            return func(*(args + fargs), **newkeywords)
        newfunc.func = func
        newfunc.args = args
        newfunc.keywords = keywords
        return newfunc

HELP_TEXT = """\
Welcome to PuDB, the Python Urwid debugger.
-------------------------------------------

(This help screen is scrollable. Hit Page Down to see more.)

Keys:
    Ctrl-p - edit preferences

    n - step over ("next")
    s - step into
    c - continue
    r/f - finish current function
    t - run to cursor
    e - show traceback [post-mortem or in exception state]

    H - move to current line (bottom of stack)
    u - move up one stack frame
    d - move down one stack frame

    o - show console/output screen

    b - toggle breakpoint
    m - open module

    j/k - up/down
    Ctrl-u/d - page up/down
    h/l - scroll left/right
    g/G - start/end
    L - show (file/line) location / go to line
    / - search
    ,/. - search next/previous

    V - focus variables
    S - focus stack
    B - focus breakpoint list
    C - focus code

    f1/?/H - show this help screen
    q - quit

    Ctrl-c - when in continue mode, break back to PuDB

    Ctrl-l - redraw screen

Command line-related:
    ! - invoke configured python command line in current environment
    Ctrl-x - toggle inline command line focus

    +/- - grow/shrink inline command line (active in command line history)
    _/= - minimize/maximize inline command line (active in command line history)

    Ctrl-v - insert newline
    Ctrl-n/p - browse command line history
    Tab - yes, there is (simple) tab completion

Sidebar-related (active in sidebar):
    +/- - grow/shrink sidebar
    _/= - minimize/maximize sidebar
    [/] - grow/shrink relative size of active sidebar box

Keys in variables list:
    \ - expand/collapse
    t/r/s/c - show type/repr/str/custom for this variable
    h - toggle highlighting
    @ - toggle repetition at top
    * - toggle private members
    w - toggle line wrapping
    n/insert - add new watch expression
    enter - edit options (also to delete)

Keys in stack list:

    enter - jump to frame

Keys in breakpoints view:

    enter - edit breakpoint
    d - delete breakpoint
    e - enable/disable breakpoint

License:
--------

PuDB is licensed to you under the MIT/X Consortium license:

Copyright (c) 2009-13 Andreas Kloeckner and contributors

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


# {{{ debugger interface

class Debugger(bdb.Bdb):
    def __init__(self, steal_output=False):
        bdb.Bdb.__init__(self)
        self.ui = DebuggerUI(self)
        self.steal_output = steal_output

        self.setup_state()

        if steal_output:
            raise NotImplementedError("output stealing")
            if PY3:
                from io import StringIO
            else:
                from cStringIO import StringIO
            self.stolen_output = sys.stderr = sys.stdout = StringIO()
            sys.stdin = StringIO("")  # avoid spurious hangs

        from pudb.settings import load_breakpoints
        for bpoint_descr in load_breakpoints():
            self.set_break(*bpoint_descr)

    def set_trace(self, frame=None):
        """Start debugging from `frame`.

        If frame is not specified, debugging starts from caller's frame.

        This is exactly the same as Bdb.set_trace(), sans the self.reset() call.
        """
        if frame is None:
            frame = sys._getframe().f_back
        # See pudb issue #52. If this works well enough we should upstream to
        # stdlib bdb.py.
        #self.reset()
        while frame:
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back
        self.set_step()
        sys.settrace(self.trace_dispatch)

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
        self.mainpyfile = ''
        self._wait_for_mainpyfile = False
        self.current_bp = None
        self.post_mortem = False

    def restart(self):
        from linecache import checkcache
        checkcache()
        self.ui.set_source_code_provider(NullSourceCodeProvider())
        self.setup_state()

    def do_clear(self, arg):
        self.clear_bpbynumber(int(arg))

    def set_frame_index(self, index):
        self.curindex = index
        if index < 0 or index >= len(self.stack):
            return

        self.curframe, lineno = self.stack[index]

        filename = self.curframe.f_code.co_filename

        import linecache
        if not linecache.getlines(filename):
            code = self.curframe.f_globals.get("_MODULE_SOURCE_CODE")
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

    def move_up_frame(self):
        if self.curindex > 0:
            self.set_frame_index(self.curindex-1)

    def move_down_frame(self):
        if self.curindex < len(self.stack)-1:
            self.set_frame_index(self.curindex+1)

    def get_shortened_stack(self, frame, tb):
        stack, index = self.get_stack(frame, tb)

        for i, (s_frame, lineno) in enumerate(stack):
            if s_frame is self.bottom_frame and index >= i:
                stack = stack[i:]
                index -= i

        return stack, index

    def interaction(self, frame, exc_tuple=None, show_exc_dialog=True):
        if exc_tuple is None:
            tb = None
        else:
            tb = exc_tuple[2]

        if frame is None and tb is not None:
            frame = tb.tb_frame

        found_bottom_frame = False
        walk_frame = frame
        while True:
            if walk_frame is self.bottom_frame:
                found_bottom_frame = True
                break
            if walk_frame is None:
                break
            walk_frame = walk_frame.f_back

        if not found_bottom_frame and not self.post_mortem:
            return

        self.stack, index = self.get_shortened_stack(frame, tb)

        if self.post_mortem:
            index = len(self.stack)-1

        self.set_frame_index(index)

        self.ui.call_with_ui(self.ui.interaction, exc_tuple,
                show_exc_dialog=show_exc_dialog)

    def get_stack_situation_id(self):
        return str(id(self.stack[self.curindex][0].f_code))

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        if self._wait_for_mainpyfile:
            return
        if self.stop_here(frame):
            self.interaction(frame)

    def user_line(self, frame):
        """This function is called when we stop or break at this line."""
        if "__exc_tuple__" in frame.f_locals:
            del frame.f_locals['__exc_tuple__']

        if self._wait_for_mainpyfile:
            if (self.mainpyfile != self.canonic(frame.f_code.co_filename)
                    or frame.f_lineno <= 0):
                return
            self._wait_for_mainpyfile = False
            self.bottom_frame = frame

        if self.get_break(self.canonic(frame.f_code.co_filename), frame.f_lineno):
            self.current_bp = (
                    self.canonic(frame.f_code.co_filename), frame.f_lineno)
        else:
            self.current_bp = None
        self.ui.update_breakpoints()

        self.interaction(frame)

    def user_return(self, frame, return_value):
        """This function is called when a return trap is set here."""
        frame.f_locals['__return__'] = return_value

        if self._wait_for_mainpyfile:
            if (self.mainpyfile != self.canonic(frame.f_code.co_filename)
                    or frame.f_lineno <= 0):
                return
            self._wait_for_mainpyfile = False
            self.bottom_frame = frame

        if "__exc_tuple__" not in frame.f_locals:
            self.interaction(frame)

    def user_exception(self, frame, exc_tuple):
        """This function is called if an exception occurs,
        but only if we are to stop at or just below this level."""
        frame.f_locals['__exc_tuple__'] = exc_tuple

        if not self._wait_for_mainpyfile:
            self.interaction(frame, exc_tuple)

    def _runscript(self, filename):
        # Start with fresh empty copy of globals and locals and tell the script
        # that it's being run as __main__ to avoid scripts being able to access
        # the debugger's namespace.
        globals_ = {"__name__": "__main__", "__file__": filename}
        locals_ = globals_

        # When bdb sets tracing, a number of call and line events happens
        # BEFORE debugger even reaches user's code (and the exact sequence of
        # events depends on python version). So we take special measures to
        # avoid stopping before we reach the main script (see user_line and
        # user_call for details).
        self._wait_for_mainpyfile = 1
        self.mainpyfile = self.canonic(filename)
        if PY3:
            statement = 'exec(compile(open("%s").read(), "%s", "exec"))' % (
                    filename, filename)
        else:
            statement = 'execfile( "%s")' % filename

        # Set up an interrupt handler
        from pudb import set_interrupt_handler
        set_interrupt_handler()

        self.run(statement, globals=globals_, locals=locals_)

# }}}


# UI stuff --------------------------------------------------------------------

from pudb.ui_tools import make_hotkey_markup, labelled_value, \
        SelectableText, SignalWrap, StackFrame, BreakpointFrame

from pudb.var_view import FrameVarInfoKeeper


# {{{ display setup

try:
    import curses
except ImportError:
    curses = None


want_curses_display = (
        CONFIG["display"] == "curses"
        or (
            CONFIG["display"] == "auto"
            and
            not os.environ.get("TERM", "").startswith("xterm")))

from urwid.raw_display import Screen as RawScreen
if want_curses_display:
    try:
        from urwid.curses_display import Screen
    except ImportError:
        Screen = RawScreen
else:
    Screen = RawScreen

del want_curses_display


class ThreadsafeScreen(Screen):
    "A Screen subclass that doesn't crash when running from a non-main thread."

    def signal_init(self):
        "Initialize signal handler, ignoring errors silently."
        try:
            super(ThreadsafeScreen, self).signal_init()
        except ValueError:
            pass

    def signal_restore(self):
        "Restore default signal handler, ignoring errors silently."
        try:
            super(ThreadsafeScreen, self).signal_restore()
        except ValueError:
            pass

# }}}


# {{{ source code providers

class SourceCodeProvider(object):
    def __ne__(self, other):
        return not (self == other)


class NullSourceCodeProvider(SourceCodeProvider):
    def __eq__(self, other):
        return type(self) == type(other)

    def identifier(self):
        return "<no source code>"

    def get_breakpoint_source_identifier(self):
        return None

    def clear_cache(self):
        pass

    def get_lines(self, debugger_ui):
        from pudb.source_view import SourceLine
        return [
                SourceLine(debugger_ui, "<no source code available>"),
                SourceLine(debugger_ui, ""),
                SourceLine(debugger_ui, "If this is generated code and you would "
                    "like the source code to show up here,"),
                SourceLine(debugger_ui, "simply set the attribute "
                    "_MODULE_SOURCE_CODE in the module in which this function"),
                SourceLine(debugger_ui, "was compiled to a string containing "
                    "the code."),
                ]


class FileSourceCodeProvider(SourceCodeProvider):
    def __init__(self, debugger, file_name):
        self.file_name = debugger.canonic(file_name)

    def __eq__(self, other):
        return (
                type(self) == type(other)
                and
                self.file_name == other.file_name)

    def identifier(self):
        return self.file_name

    def get_breakpoint_source_identifier(self):
        return self.file_name

    def clear_cache(self):
        from linecache import clearcache
        clearcache()

    def get_lines(self, debugger_ui):
        from pudb.source_view import SourceLine, format_source

        if self.file_name == "<string>":
            return [SourceLine(self, self.file_name)]

        breakpoints = debugger_ui.debugger.get_file_breaks(self.file_name)
        try:
            from linecache import getlines
            lines = getlines(self.file_name)

            from pudb.lowlevel import detect_encoding
            source_enc, _ = detect_encoding(getattr(iter(lines), _next))

            decoded_lines = []
            for l in lines:
                if hasattr(l, "decode"):
                    decoded_lines.append(l.decode(source_enc))
                else:
                    decoded_lines.append(l)

            return format_source(debugger_ui, decoded_lines, set(breakpoints))
        except:
            from pudb.lowlevel import format_exception
            self.message("Could not load source file '%s':\n\n%s" % (
                self.file_name, "".join(format_exception(sys.exc_info()))),
                title="Source Code Load Error")
            return [SourceLine(self,
                "Error while loading '%s'." % self.file_name)]


class DirectSourceCodeProvider(SourceCodeProvider):
    def __init__(self, func_name, code):
        self.function_name = func_name
        self.code = code

    def __eq__(self, other):
        return (
                type(self) == type(other)
                and
                self.function_name == other.function_name
                and
                self.code is other.code)

    def identifier(self):
        return "<source code of function %s>" % self.function_name

    def get_breakpoint_source_identifier(self):
        return None

    def clear_cache(self):
        pass

    def get_lines(self, debugger_ui):
        from pudb.source_view import format_source

        lines = self.code.split("\n")

        from pudb.lowlevel import detect_encoding
        source_enc, _ = detect_encoding(getattr(iter(lines), _next))

        decoded_lines = []
        for i, l in enumerate(lines):
            if hasattr(l, "decode"):
                l = l.decode(source_enc)
            else:
                l = l.decode(source_enc)

            if i+1 < len(lines):
                l += "\n"

            decoded_lines.append(l)

        return format_source(debugger_ui, decoded_lines, set())

# }}}


class DebuggerUI(FrameVarInfoKeeper):
    # {{{ constructor

    def __init__(self, dbg):
        FrameVarInfoKeeper.__init__(self)

        self.debugger = dbg

        from urwid import AttrMap

        from pudb.ui_tools import SearchController
        self.search_controller = SearchController(self)

        self.last_module_filter = ""

        # {{{ build ui

        # {{{ left/source column

        self.source = urwid.SimpleListWalker([])
        self.source_list = urwid.ListBox(self.source)
        self.source_sigwrap = SignalWrap(self.source_list)
        self.source_attr = urwid.AttrMap(self.source_sigwrap, "source")
        self.source_hscroll_start = 0

        self.cmdline_history = []
        self.cmdline_history_position = -1

        self.cmdline_contents = urwid.SimpleFocusListWalker([])
        self.cmdline_list = urwid.ListBox(self.cmdline_contents)
        self.cmdline_edit = urwid.Edit([
            ("command line prompt", ">>> ")
            ])
        cmdline_edit_attr = urwid.AttrMap(self.cmdline_edit, "command line edit")
        self.cmdline_edit_sigwrap = SignalWrap(
                cmdline_edit_attr, is_preemptive=True)

        def clear_cmdline_history(btn):
            del self.cmdline_contents[:]

        self.cmdline_edit_bar = urwid.Columns([
                self.cmdline_edit_sigwrap,
                ("fixed", 10, AttrMap(
                    urwid.Button("Clear", clear_cmdline_history),
                    "command line clear button", "command line focused button"))
                ])

        self.cmdline_pile = urwid.Pile([
            ("flow", urwid.Text("Command line: [Ctrl-X]")),
            ("weight", 1, urwid.AttrMap(self.cmdline_list, "command line output")),
            ("flow", self.cmdline_edit_bar),
            ])
        self.cmdline_sigwrap = SignalWrap(
                urwid.AttrMap(self.cmdline_pile, None, "focused sidebar")
                )

        self.lhs_col = urwid.Pile([
            ("weight", 5, self.source_attr),
            ("weight", 1, self.cmdline_sigwrap),
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
            ("weight", float(CONFIG["variables_weight"]), AttrMap(urwid.Pile([
                ("flow", urwid.Text(make_hotkey_markup("_Variables:"))),
                AttrMap(self.var_list, "variables"),
                ]), None, "focused sidebar"),),
            ("weight", float(CONFIG["stack_weight"]), AttrMap(urwid.Pile([
                ("flow", urwid.Text(make_hotkey_markup("_Stack:"))),
                AttrMap(self.stack_list, "stack"),
                ]), None, "focused sidebar"),),
            ("weight", float(CONFIG["breakpoints_weight"]), AttrMap(urwid.Pile([
                ("flow", urwid.Text(make_hotkey_markup("_Breakpoints:"))),
                AttrMap(self.bp_list, "breakpoint"),
                ]), None, "focused sidebar"),),
            ])
        self.rhs_col_sigwrap = SignalWrap(self.rhs_col)

        # }}}

        self.columns = urwid.Columns(
                    [
                        ("weight", 1, self.lhs_col),
                        ("weight", float(CONFIG["sidebar_width"]),
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

            _, weight = self.rhs_col.item_types[index]

            if direction < 0:
                if weight > 1/5:
                    weight /= 1.25
            else:
                if weight < 5:
                    weight *= 1.25

            CONFIG[name+"_weight"] = weight
            save_config(CONFIG)
            self.rhs_col.item_types[index] = "weight", weight
            self.rhs_col._invalidate()

        # {{{ variables listeners

        def change_var_state(w, size, key):
            var, pos = self.var_list._w.get_focus()

            iinfo = self.get_frame_var_info(read_only=False) \
                    .get_inspect_info(var.id_path, read_only=False)

            if key == "\\":
                iinfo.show_detail = not iinfo.show_detail
            elif key == "t":
                iinfo.display_type = "type"
            elif key == "r":
                iinfo.display_type = "repr"
            elif key == "s":
                iinfo.display_type = "str"
            elif key == "c":
                iinfo.display_type = CONFIG["custom_stringifier"]
            elif key == "h":
                iinfo.highlighted = not iinfo.highlighted
            elif key == "@":
                iinfo.repeated_at_top = not iinfo.repeated_at_top
            elif key == "*":
                iinfo.show_private_members = not iinfo.show_private_members
            elif key == "w":
                iinfo.wrap = not iinfo.wrap

            self.update_var_view()

        def edit_inspector_detail(w, size, key):
            var, pos = self.var_list._w.get_focus()

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
                id_segment = [urwid.AttrMap(watch_edit, "value"), urwid.Text("")]

                buttons.extend([None, ("Delete", "del")])

                title = "Watch Expression Options"
            else:
                id_segment = [
                        labelled_value("Identifier Path: ", var.id_path),
                        urwid.Text(""),
                        ]

                title = "Variable Inspection Options"

            rb_grp = []
            rb_show_type = urwid.RadioButton(rb_grp, "Show Type",
                    iinfo.display_type == "type")
            rb_show_repr = urwid.RadioButton(rb_grp, "Show repr()",
                    iinfo.display_type == "repr")
            rb_show_str = urwid.RadioButton(rb_grp, "Show str()",
                    iinfo.display_type == "str")
            rb_show_custom = urwid.RadioButton(rb_grp, "Show custom (set in prefs)",
                    iinfo.display_type == CONFIG["custom_stringifier"])

            wrap_checkbox = urwid.CheckBox("Line Wrap", iinfo.wrap)
            expanded_checkbox = urwid.CheckBox("Expanded", iinfo.show_detail)
            highlighted_checkbox = urwid.CheckBox("Highlighted", iinfo.highlighted)
            repeated_at_top_checkbox = urwid.CheckBox(
                    "Repeated at top", iinfo.repeated_at_top)
            show_private_checkbox = urwid.CheckBox(
                    "Show private members", iinfo.show_private_members)

            lb = urwid.ListBox(urwid.SimpleListWalker(
                id_segment+rb_grp+[
                    urwid.Text(""),
                    wrap_checkbox,
                    expanded_checkbox,
                    highlighted_checkbox,
                    repeated_at_top_checkbox,
                    show_private_checkbox,
                ]))

            result = self.dialog(lb, buttons, title=title)

            if result is True:
                iinfo.show_detail = expanded_checkbox.get_state()
                iinfo.wrap = wrap_checkbox.get_state()
                iinfo.highlighted = highlighted_checkbox.get_state()
                iinfo.repeated_at_top = repeated_at_top_checkbox.get_state()
                iinfo.show_private_members = show_private_checkbox.get_state()

                if rb_show_type.get_state():
                    iinfo.display_type = "type"
                elif rb_show_repr.get_state():
                    iinfo.display_type = "repr"
                elif rb_show_str.get_state():
                    iinfo.display_type = "str"
                elif rb_show_custom.get_state():
                    iinfo.display_type = CONFIG["custom_stringifier"]

                if var.watch_expr is not None:
                    var.watch_expr.expression = watch_edit.get_edit_text()

            elif result == "del":
                for i, watch_expr in enumerate(fvi.watches):
                    if watch_expr is var.watch_expr:
                        del fvi.watches[i]

            self.update_var_view()

        def insert_watch(w, size, key):
            watch_edit = urwid.Edit([
                ("label", "Watch expression: ")
                ])

            if self.dialog(
                    urwid.ListBox(urwid.SimpleListWalker([
                        urwid.AttrMap(watch_edit, "value")
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
        self.var_list.listen("t", change_var_state)
        self.var_list.listen("r", change_var_state)
        self.var_list.listen("s", change_var_state)
        self.var_list.listen("c", change_var_state)
        self.var_list.listen("h", change_var_state)
        self.var_list.listen("@", change_var_state)
        self.var_list.listen("*", change_var_state)
        self.var_list.listen("w", change_var_state)
        self.var_list.listen("enter", edit_inspector_detail)
        self.var_list.listen("n", insert_watch)
        self.var_list.listen("insert", insert_watch)

        self.var_list.listen("[", partial(change_rhs_box, 'variables', 0, -1))
        self.var_list.listen("]", partial(change_rhs_box, 'variables', 0, 1))

        # }}}

        # {{{ stack listeners
        def examine_frame(w, size, key):
            _, pos = self.stack_list._w.get_focus()
            self.debugger.set_frame_index(self.translate_ui_stack_index(pos))

        self.stack_list.listen("enter", examine_frame)

        def move_stack_top(w, size, key):
            self.debugger.set_frame_index(len(self.debugger.stack)-1)

        def move_stack_up(w, size, key):
            self.debugger.move_up_frame()

        def move_stack_down(w, size, key):
            self.debugger.move_down_frame()

        self.stack_list.listen("H", move_stack_top)
        self.stack_list.listen("u", move_stack_up)
        self.stack_list.listen("d", move_stack_down)

        self.stack_list.listen("[", partial(change_rhs_box, 'stack', 1, -1))
        self.stack_list.listen("]", partial(change_rhs_box, 'stack', 1, 1))

        # }}}

        # {{{ breakpoint listeners
        def save_breakpoints(w, size, key):
            self.debugger.save_breakpoints()

        def delete_breakpoint(w, size, key):
            bp_source_identifier = \
                    self.source_code_provider.get_breakpoint_source_identifier()

            if bp_source_identifier is None:
                self.message(
                    "Cannot currently delete a breakpoint here--"
                    "source code does not correspond to a file location. "
                    "(perhaps this is generated code)")

            bp_list = self._get_bp_list()
            if bp_list:
                _, pos = self.bp_list._w.get_focus()
                bp = bp_list[pos]
                if bp_source_identifier == bp.file and bp.line-1 < len(self.source):
                    self.source[bp.line-1].set_breakpoint(False)

                err = self.debugger.clear_break(bp.file, bp.line)
                if err:
                    self.message("Error clearing breakpoint:\n" + err)
                else:
                    self.update_breakpoints()

        def enable_disable_breakpoint(w, size, key):
            bp_entry, pos = self.bp_list._w.get_focus()

            if bp_entry is None:
                return

            bp = self._get_bp_list()[pos]
            bp.enabled = not bp.enabled

            self.update_breakpoints()

        def examine_breakpoint(w, size, key):
            bp_entry, pos = self.bp_list._w.get_focus()

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
                urwid.AttrMap(cond_edit, "value", "value"),
                urwid.AttrMap(ign_count_edit, "value", "value"),
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
                self.columns.set_focus(0)
            elif result == "del":
                bp_source_identifier = \
                        self.source_code_provider.get_breakpoint_source_identifier()

                if bp_source_identifier is None:
                    self.message(
                        "Cannot currently delete a breakpoint here--"
                        "source code does not correspond to a file location. "
                        "(perhaps this is generated code)")

                if bp_source_identifier == bp.file:
                    self.source[bp.line-1].set_breakpoint(False)

                err = self.debugger.clear_break(bp.file, bp.line)
                if err:
                    self.message("Error clearing breakpoint:\n" + err)
                else:
                    self.update_breakpoints()

        self.bp_list.listen("enter", examine_breakpoint)
        self.bp_list.listen("d", delete_breakpoint)
        self.bp_list.listen("s", save_breakpoints)
        self.bp_list.listen("e", enable_disable_breakpoint)

        self.bp_list.listen("[", partial(change_rhs_box, 'breakpoints', 2, -1))
        self.bp_list.listen("]", partial(change_rhs_box, 'breakpoints', 2, 1))

        # }}}

        # {{{ source listeners

        def end():
            self.debugger.save_breakpoints()
            self.quit_event_loop = True

        def next(w, size, key):
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
                sline, pos = self.source.get_focus()
                lineno = pos+1

                bp_source_identifier = \
                        self.source_code_provider.get_breakpoint_source_identifier()

                if bp_source_identifier is None:
                    self.message(
                        "Cannot currently set a breakpoint here--"
                        "source code does not correspond to a file location. "
                        "(perhaps this is generated code)")

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

        def move_home(w, size, key):
            self.source.set_focus(0)

        def move_end(w, size, key):
            self.source.set_focus(len(self.source)-1)

        def go_to_line(w, size, key):
            _, line = self.source.get_focus()

            lineno_edit = urwid.IntEdit([
                ("label", "Line number: ")
                ], line+1)

            if self.dialog(
                    urwid.ListBox(urwid.SimpleListWalker([
                        labelled_value("File :",
                            self.source_code_provider.identifier()),
                        urwid.AttrMap(lineno_edit, "value")
                        ])),
                    [
                        ("OK", True),
                        ("Cancel", False),
                        ], title="Go to Line Number"):
                lineno = min(max(0, int(lineno_edit.value())-1), len(self.source)-1)
                self.source.set_focus(lineno)

        def move_down(w, size, key):
            w.keypress(size, "down")

        def move_up(w, size, key):
            w.keypress(size, "up")

        def page_down(w, size, key):
            w.keypress(size, "page down")

        def page_up(w, size, key):
            w.keypress(size, "page up")

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
                    self.source_code_provider.get_breakpoint_source_identifier()

            if bp_source_identifier:
                sline, pos = self.source.get_focus()
                lineno = pos+1

                existing_breaks = self.debugger.get_breaks(
                        bp_source_identifier, lineno)
                if existing_breaks:
                    err = self.debugger.clear_break(bp_source_identifier, lineno)
                    sline.set_breakpoint(False)
                else:
                    from pudb.lowlevel import get_breakpoint_invalid_reason
                    invalid_reason = get_breakpoint_invalid_reason(
                            bp_source_identifier, pos+1)

                    if invalid_reason is not None:
                        do_set = not self.dialog(
                                urwid.ListBox(urwid.SimpleListWalker([
                                    urwid.Text("The breakpoint you just set may be "
                                        "invalid, for the following reason:\n\n"
                                        + invalid_reason),
                                    ])), [
                                        ("Cancel", True),
                                        ("Set Anyway", False),
                                        ], title="Possibly Invalid Breakpoint",
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

        def pick_module(w, size, key):
            from os.path import splitext

            import sys

            def mod_exists(mod):
                if not hasattr(mod, "__file__"):
                    return False
                filename = mod.__file__

                base, ext = splitext(filename)
                ext = ext.lower()

                from os.path import exists

                if ext == ".pyc":
                    return exists(base+".py")
                else:
                    return ext == ".py"

            new_mod_text = SelectableText("-- update me --")
            new_mod_entry = urwid.AttrMap(new_mod_text,
                    None, "focused selectable")

            def build_filtered_mod_list(filt_string=""):
                modules = sorted(name
                        for name, mod in sys.modules.items()
                        if mod_exists(mod))

                result = [urwid.AttrMap(SelectableText(mod),
                        None, "focused selectable")
                        for mod in modules if filt_string in mod]
                new_mod_text.set_text("<<< IMPORT MODULE '%s' >>>" % filt_string)
                result.append(new_mod_entry)
                return result

            def show_mod(mod):
                filename = self.debugger.canonic(mod.__file__)

                base, ext = splitext(filename)
                if ext == ".pyc":
                    ext = ".py"
                    filename = base+".py"

                self.set_source_code_provider(
                        FileSourceCodeProvider(self.debugger, filename))
                self.source_list.set_focus(0)

            class FilterEdit(urwid.Edit):
                def keypress(self, size, key):
                    result = urwid.Edit.keypress(self, size, key)

                    if result is None:
                        mod_list[:] = build_filtered_mod_list(
                                self.get_edit_text())

                    return result

            filt_edit = FilterEdit([("label", "Filter: ")],
                    self.last_module_filter)

            mod_list = urwid.SimpleListWalker(
                    build_filtered_mod_list(filt_edit.get_edit_text()))
            lb = urwid.ListBox(mod_list)

            w = urwid.Pile([
                ("flow", urwid.AttrMap(filt_edit, "value")),
                ("fixed", 1, urwid.SolidFill()),
                urwid.AttrMap(lb, "selectable")])

            while True:
                result = self.dialog(w, [
                    ("OK", True),
                    ("Cancel", False),
                    ("Reload", "reload"),

                    ], title="Pick Module")
                self.last_module_filter = filt_edit.get_edit_text()

                if result is True:
                    widget, pos = lb.get_focus()
                    if widget is new_mod_entry:
                        new_mod_name = filt_edit.get_edit_text()
                        try:
                            __import__(str(new_mod_name))
                        except:
                            from pudb.lowlevel import format_exception

                            self.message("Could not import module '%s':\n\n%s" % (
                                new_mod_name, "".join(
                                    format_exception(sys.exc_info()))),
                                title="Import Error")
                        else:
                            show_mod(sys.modules[str(new_mod_name)])
                            break
                    else:
                        show_mod(sys.modules[widget.base_widget.get_text()[0]])
                        break
                elif result is False:
                    break
                elif result == "reload":
                    widget, pos = lb.get_focus()
                    if widget is not new_mod_entry:
                        mod_name = widget.base_widget.get_text()[0]
                        mod = sys.modules[mod_name]
                        reload(mod)
                        self.message("'%s' was successfully reloaded." % mod_name)

                        if self.source_code_provider is not None:
                            self.source_code_provider.clear_cache()

                        self.set_source_code_provider(self.source_code_provider,
                                force_update=True)

                        _, pos = self.stack_list._w.get_focus()
                        self.debugger.set_frame_index(
                                self.translate_ui_stack_index(pos))

        self.source_sigwrap.listen("n", next)
        self.source_sigwrap.listen("s", step)
        self.source_sigwrap.listen("f", finish)
        self.source_sigwrap.listen("r", finish)
        self.source_sigwrap.listen("c", cont)
        self.source_sigwrap.listen("t", run_to_cursor)

        self.source_sigwrap.listen("j", move_down)
        self.source_sigwrap.listen("k", move_up)
        self.source_sigwrap.listen("ctrl d", page_down)
        self.source_sigwrap.listen("ctrl u", page_up)
        self.source_sigwrap.listen("ctrl f", page_down)
        self.source_sigwrap.listen("ctrl b", page_up)
        self.source_sigwrap.listen("h", scroll_left)
        self.source_sigwrap.listen("l", scroll_right)

        self.source_sigwrap.listen("/", search)
        self.source_sigwrap.listen(",", search_previous)
        self.source_sigwrap.listen(".", search_next)

        self.source_sigwrap.listen("home", move_home)
        self.source_sigwrap.listen("end", move_end)
        self.source_sigwrap.listen("g", move_home)
        self.source_sigwrap.listen("G", move_end)
        self.source_sigwrap.listen("L", go_to_line)

        self.source_sigwrap.listen("b", toggle_breakpoint)
        self.source_sigwrap.listen("m", pick_module)

        self.source_sigwrap.listen("H", move_stack_top)
        self.source_sigwrap.listen("u", move_stack_up)
        self.source_sigwrap.listen("d", move_stack_down)

        # }}}

        # {{{ command line listeners

        def cmdline_get_namespace():
            curframe = self.debugger.curframe

            from pudb.shell import SetPropagatingDict
            return SetPropagatingDict(
                    [curframe.f_locals, curframe.f_globals],
                    curframe.f_locals)

        def add_cmdline_content(s, attr):
            s = s.rstrip("\n")

            from pudb.ui_tools import SelectableText
            self.cmdline_contents.append(
                    urwid.AttrMap(SelectableText(s),
                        attr, "focused "+attr))

            # scroll to end of last entry
            self.cmdline_list.set_focus_valign("bottom")
            self.cmdline_list.set_focus(len(self.cmdline_contents) - 1,
                    coming_from="above")

        def cmdline_tab_complete(w, size, key):
            from rlcompleter import Completer

            text = self.cmdline_edit.edit_text
            pos = self.cmdline_edit.edit_pos

            chopped_text = text[:pos]
            suffix = text[pos:]

            # stolen from readline in the Python interactive shell
            delimiters = " \t\n`~!@#$%^&*()-=+[{]}\\|;:\'\",<>/?"

            complete_start_index = max(
                    chopped_text.rfind(delim_i)
                    for delim_i in delimiters)

            if complete_start_index == -1:
                prefix = ""
            else:
                prefix = chopped_text[:complete_start_index+1]
                chopped_text = chopped_text[complete_start_index+1:]

            state = 0
            chopped_completions = []
            completer = Completer(cmdline_get_namespace())
            while True:
                completion = completer.complete(chopped_text, state)

                if not isinstance(completion, str):
                    break

                chopped_completions.append(completion)
                state += 1

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
                    len(completed_chopped_text) == len(chopped_text)
                    and len(chopped_completions) > 1):
                add_cmdline_content(
                        "   ".join(chopped_completions),
                        "command line output")
                return

            self.cmdline_edit.edit_text = \
                    prefix+completed_chopped_text+suffix
            self.cmdline_edit.edit_pos = len(prefix) + len(completed_chopped_text)

        def cmdline_append_newline(w, size, key):
            self.cmdline_edit.insert_text("\n")

        def cmdline_exec(w, size, key):
            cmd = self.cmdline_edit.get_edit_text()
            if not cmd:
                # blank command -> refuse service
                return

            add_cmdline_content(">>> " + cmd, "command line input")

            if not self.cmdline_history or cmd != self.cmdline_history[-1]:
                self.cmdline_history.append(cmd)

            self.cmdline_history_position = -1

            prev_sys_stdin = sys.stdin
            prev_sys_stdout = sys.stdout
            prev_sys_stderr = sys.stderr

            if PY3:
                from io import StringIO
            else:
                from cStringIO import StringIO

            sys.stdin = None
            sys.stderr = sys.stdout = StringIO()
            try:
                eval(compile(cmd, "<pudb command line>", 'single'),
                        cmdline_get_namespace())
            except:
                tp, val, tb = sys.exc_info()

                import traceback

                tblist = traceback.extract_tb(tb)
                del tblist[:1]
                tb_lines = traceback.format_list(tblist)
                if tb_lines:
                    tb_lines.insert(0, "Traceback (most recent call last):\n")
                tb_lines[len(tb_lines):] = traceback.format_exception_only(tp, val)

                add_cmdline_content("".join(tb_lines), "command line error")
            else:
                self.cmdline_edit.set_edit_text("")
            finally:
                if sys.stdout.getvalue():
                    add_cmdline_content(sys.stdout.getvalue(), "command line output")

                sys.stdin = prev_sys_stdin
                sys.stdout = prev_sys_stdout
                sys.stderr = prev_sys_stderr

        def cmdline_history_browse(direction):
            if self.cmdline_history_position == -1:
                self.cmdline_history_position = len(self.cmdline_history)

            self.cmdline_history_position += direction

            if 0 <= self.cmdline_history_position < len(self.cmdline_history):
                self.cmdline_edit.edit_text = \
                        self.cmdline_history[self.cmdline_history_position]
            else:
                self.cmdline_history_position = -1
                self.cmdline_edit.edit_text = ""
            self.cmdline_edit.edit_pos = len(self.cmdline_edit.edit_text)

        def cmdline_history_prev(w, size, key):
            cmdline_history_browse(-1)

        def cmdline_history_next(w, size, key):
            cmdline_history_browse(1)

        def toggle_cmdline_focus(w, size, key):
            self.columns.set_focus(self.lhs_col)
            if self.lhs_col.get_focus() is self.cmdline_sigwrap:
                self.lhs_col.set_focus(self.source_attr)
            else:
                self.cmdline_pile.set_focus(self.cmdline_edit_bar)
                self.lhs_col.set_focus(self.cmdline_sigwrap)

        self.cmdline_edit_sigwrap.listen("tab", cmdline_tab_complete)
        self.cmdline_edit_sigwrap.listen("ctrl v", cmdline_append_newline)
        self.cmdline_edit_sigwrap.listen("enter", cmdline_exec)
        self.cmdline_edit_sigwrap.listen("ctrl n", cmdline_history_next)
        self.cmdline_edit_sigwrap.listen("ctrl p", cmdline_history_prev)
        self.cmdline_edit_sigwrap.listen("esc", toggle_cmdline_focus)
        self.cmdline_edit_sigwrap.listen("ctrl d", toggle_cmdline_focus)

        self.top.listen("ctrl x", toggle_cmdline_focus)

        # {{{ command line sizing

        def max_cmdline(w, size, key):
            self.lhs_col.item_types[-1] = "weight", 5
            self.lhs_col._invalidate()

        def min_cmdline(w, size, key):
            self.lhs_col.item_types[-1] = "weight", 1/2
            self.lhs_col._invalidate()

        def grow_cmdline(w, size, key):
            _, weight = self.lhs_col.item_types[-1]

            if weight < 5:
                weight *= 1.25
                self.lhs_col.item_types[-1] = "weight", weight
                self.lhs_col._invalidate()

        def shrink_cmdline(w, size, key):
            _, weight = self.lhs_col.item_types[-1]

            if weight > 1/2:
                weight /= 1.25
                self.lhs_col.item_types[-1] = "weight", weight
                self.lhs_col._invalidate()

        self.cmdline_sigwrap.listen("=", max_cmdline)
        self.cmdline_sigwrap.listen("+", grow_cmdline)
        self.cmdline_sigwrap.listen("_", min_cmdline)
        self.cmdline_sigwrap.listen("-", shrink_cmdline)

        # }}}

        # }}}

        # {{{ sidebar sizing

        def max_sidebar(w, size, key):
            from pudb.settings import save_config

            weight = 5
            CONFIG["sidebar_width"] = weight
            save_config(CONFIG)

            self.columns.column_types[1] = "weight", weight
            self.columns._invalidate()

        def min_sidebar(w, size, key):
            from pudb.settings import save_config

            weight = 1/5
            CONFIG["sidebar_width"] = weight
            save_config(CONFIG)

            self.columns.column_types[1] = "weight", weight
            self.columns._invalidate()

        def grow_sidebar(w, size, key):
            from pudb.settings import save_config

            _, weight = self.columns.column_types[1]

            if weight < 5:
                weight *= 1.25
                CONFIG["sidebar_width"] = weight
                save_config(CONFIG)
                self.columns.column_types[1] = "weight", weight
                self.columns._invalidate()

        def shrink_sidebar(w, size, key):
            from pudb.settings import save_config

            _, weight = self.columns.column_types[1]

            if weight > 1/5:
                weight /= 1.25
                CONFIG["sidebar_width"] = weight
                save_config(CONFIG)
                self.columns.column_types[1] = "weight", weight
                self.columns._invalidate()

        self.rhs_col_sigwrap.listen("=", max_sidebar)
        self.rhs_col_sigwrap.listen("+", grow_sidebar)
        self.rhs_col_sigwrap.listen("_", min_sidebar)
        self.rhs_col_sigwrap.listen("-", shrink_sidebar)

        # }}}

        # {{{ top-level listeners

        def show_output(w, size, key):
            self.screen.stop()
            raw_input("Hit Enter to return:")
            self.screen.start()

        def reload_breakpoints(w, size, key):
            self.debugger.clear_all_breaks()
            from pudb.settings import load_breakpoints
            for bpoint_descr in load_breakpoints():
                dbg.set_break(*bpoint_descr)
            self.update_breakpoints()

        def show_traceback(w, size, key):
            if self.current_exc_tuple is not None:
                from pudb.lowlevel import format_exception

                result = self.dialog(
                        urwid.ListBox(urwid.SimpleListWalker([urwid.Text(
                            "".join(format_exception(self.current_exc_tuple)))])),
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
            self.screen.stop()

            if not hasattr(self, "have_been_to_cmdline"):
                self.have_been_to_cmdline = True
                first_cmdline_run = True
            else:
                first_cmdline_run = False

            curframe = self.debugger.curframe

            import pudb.shell as shell
            if shell.HAVE_IPYTHON and CONFIG["shell"] == "ipython":
                runner = shell.run_ipython_shell
            elif shell.HAVE_BPYTHON and CONFIG["shell"] == "bpython":
                runner = shell.run_bpython_shell
            else:
                runner = shell.run_classic_shell

            runner(curframe.f_locals, curframe.f_globals,
                    first_cmdline_run)

            self.screen.start()

            self.update_var_view()

        def run_cmdline(w, size, key):
            if CONFIG["shell"] == "internal":
                return toggle_cmdline_focus(w, size, key)
            else:
                return run_external_cmdline(w, size, key)

        def focus_code(w, size, key):
            self.columns.set_focus(self.lhs_col)
            self.lhs_col.set_focus(self.source_attr)

        class RHColumnFocuser:
            def __init__(self, idx):
                self.idx = idx

            def __call__(subself, w, size, key):
                self.columns.set_focus(self.rhs_col_sigwrap)
                self.rhs_col.set_focus(self.rhs_col.widget_list[subself.idx])

        def quit(w, size, key):
            self.debugger.set_quit()
            end()

        def do_edit_config(w, size, key):
            self.run_edit_config()

        def redraw_screen(w, size, key):
            self.screen.clear()

        def help(w, size, key):
            self.message(HELP_TEXT, title="PuDB Help")

        self.top.listen("o", show_output)
        self.top.listen("ctrl r", reload_breakpoints)
        self.top.listen("!", run_cmdline)
        self.top.listen("e", show_traceback)

        self.top.listen("C", focus_code)
        self.top.listen("V", RHColumnFocuser(0))
        self.top.listen("S", RHColumnFocuser(1))
        self.top.listen("B", RHColumnFocuser(2))

        self.top.listen("q", quit)
        self.top.listen("ctrl p", do_edit_config)
        self.top.listen("ctrl l", redraw_screen)
        self.top.listen("f1", help)
        self.top.listen("?", help)

        # }}}

        # {{{ setup

        self.screen = ThreadsafeScreen()

        if curses:
            try:
                curses.setupterm()
            except:
                # Something went wrong--oh well. Nobody will die if their
                # 256 color support breaks. Just carry on without it.
                # https://github.com/inducer/pudb/issues/78
                pass
            else:
                color_support = curses.tigetnum('colors')

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

    def translate_ui_stack_index(self, index):
        # note: self-inverse

        if CONFIG["current_stack_frame"] == "top":
            return len(self.debugger.stack)-1-index
        elif CONFIG["current_stack_frame"] == "bottom":
            return index
        else:
            raise ValueError("invalid value for 'current_stack_frame' pref")

    def message(self, msg, title="Message", **kwargs):
        self.call_with_ui(self.dialog,
                urwid.ListBox(urwid.SimpleListWalker([urwid.Text(msg)])),
                [("OK", True)], title=title, **kwargs)

    def run_edit_config(self):
        from pudb.settings import edit_config, save_config
        edit_config(self, CONFIG)
        save_config(CONFIG)

    def dialog(self, content, buttons_and_results,
            title=None, bind_enter_esc=True, focus_buttons=False,
            extra_bindings=[]):
        class ResultSetter:
            def __init__(subself, res):
                subself.res = res

            def __call__(subself, btn):
                self.quit_event_loop = [subself.res]

        Attr = urwid.AttrMap

        if bind_enter_esc:
            content = SignalWrap(content)

            def enter(w, size, key):
                self.quit_event_loop = [True]

            def esc(w, size, key):
                self.quit_event_loop = [False]

            content.listen("enter", enter)
            content.listen("esc", esc)

        button_widgets = []
        for btn_descr in buttons_and_results:
            if btn_descr is None:
                button_widgets.append(urwid.Text(""))
            else:
                btn_text, btn_result = btn_descr
                button_widgets.append(
                        Attr(urwid.Button(btn_text, ResultSetter(btn_result)),
                            "button", "focused button"))

        w = urwid.Columns([
            content,
            ("fixed", 15, urwid.ListBox(urwid.SimpleListWalker(button_widgets))),
            ], dividechars=1)

        if focus_buttons:
            w.set_focus_column(1)

        if title is not None:
            w = urwid.Pile([
                ("flow", urwid.AttrMap(
                    urwid.Text(title, align="center"),
                    "dialog title")),
                ("fixed", 1, urwid.SolidFill()),
                w])

        class ResultSetter:
            def __init__(subself, res):
                subself.res = res

            def __call__(subself, w, size, key):
                self.quit_event_loop = [subself.res]

        w = SignalWrap(w)
        for key, binding in extra_bindings:
            if isinstance(binding, str):
                w.listen(key, ResultSetter(binding))
            else:
                w.listen(key, binding)

        w = urwid.LineBox(w)

        w = urwid.Overlay(w, self.top,
                align="center",
                valign="middle",
                width=('relative', 75),
                height=('relative', 75),
                )
        w = Attr(w, "background")

        return self.event_loop(w)[0]

    @staticmethod
    def setup_palette(screen):
        may_use_fancy_formats = not hasattr(urwid.escape, "_fg_attr_xterm")

        from pudb.theme import get_palette
        screen.register_palette(
                get_palette(may_use_fancy_formats, CONFIG["theme"]))

    def show_exception_dialog(self, exc_tuple):
        from pudb.lowlevel import format_exception

        tb_txt = "".join(format_exception(exc_tuple))
        while True:
            res = self.dialog(
                    urwid.ListBox(urwid.SimpleListWalker([urwid.Text(
                        "The program has terminated abnormally because of "
                        "an exception.\n\n"
                        "A full traceback is below. You may recall this "
                        "traceback at any time using the 'e' key. "
                        "The debugger has entered post-mortem mode and will "
                        "prevent further state changes.\n\n"
                        + tb_txt)])),
                    title="Program Terminated for Uncaught Exception",
                    buttons_and_results=[
                        ("OK", True),
                        ("Save traceback", "save"),
                        ])

            if res in [True, False]:
                break

            if res == "save":
                try:
                    n = 0
                    from os.path import exists
                    while True:
                        if n:
                            fn = "traceback-%d.txt" % n
                        else:
                            fn = "traceback.txt"

                        if not exists(fn):
                            outf = open(fn, "w")
                            try:
                                outf.write(tb_txt)
                            finally:
                                outf.close()

                            self.message("Traceback saved as %s." % fn,
                                    title="Success")

                            break

                        n += 1

                except Exception:
                    io_tb_txt = "".join(format_exception(sys.exc_info()))
                    self.message(
                            "An error occurred while trying to write "
                            "the traceback:\n\n" + io_tb_txt,
                            title="I/O error")

    # }}}

    # {{{ UI enter/exit

    def show(self):
        if self.show_count == 0:
            self.screen.start()
        self.show_count += 1

    def hide(self):
        self.show_count -= 1
        if self.show_count == 0:
            self.screen.stop()

    def call_with_ui(self, f, *args, **kwargs):
        self.show()
        try:
            return f(*args, **kwargs)
        finally:
            self.hide()

    # }}}

    # {{{ interaction

    def event_loop(self, toplevel=None):
        prev_quit_loop = self.quit_event_loop

        try:
            import pygments  # noqa
        except ImportError:
            if not hasattr(self, "pygments_message_shown"):
                self.pygments_message_shown = True
                self.message("Package 'pygments' not found. "
                        "Syntax highlighting disabled.")

        WELCOME_LEVEL = "e022"
        if CONFIG["seen_welcome"] < WELCOME_LEVEL:
            CONFIG["seen_welcome"] = WELCOME_LEVEL
            from pudb import VERSION
            self.message("Welcome to PudB %s!\n\n"
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

                    "\nChanges in version 2014.1:\n\n"
                    "- Make prompt-on-quit optional (Mike Burr)\n"
                    "- Make tab completion in the built-in shell saner\n"
                    "- Fix handling of unicode source\n  (reported by Morten Nielsen and Buck Golemon)\n"

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
                    "- Suport for custom stringifiers "
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
                    "- Line numbers (optional)\n"
                    % VERSION)
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

                for k in keys:
                    if k == "window resize":
                        self.size = self.screen.get_cols_rows()
                    else:
                        toplevel.keypress(self.size, k)

            return self.quit_event_loop
        finally:
            self.quit_event_loop = prev_quit_loop

    # }}}

    # {{{ debugger-facing interface

    def interaction(self, exc_tuple, show_exc_dialog=True):
        self.current_exc_tuple = exc_tuple

        from pudb import VERSION
        caption = [(None,
            "PuDB %s - ?:help  n:next  s:step into  b:breakpoint  "
            "!:python command line"
            % VERSION)]

        if self.debugger.post_mortem:
            if show_exc_dialog and exc_tuple is not None:
                self.show_exception_dialog(exc_tuple)

            caption.extend([
                (None, " "),
                ("warning", "[POST-MORTEM MODE]")
                ])
        elif exc_tuple is not None:
            caption.extend([
                (None, " "),
                ("warning", "[PROCESSING EXCEPTION - hit 'e' to examine]")
                ])

        self.caption.set_text(caption)
        self.event_loop()

    def set_source_code_provider(self, source_code_provider, force_update=False):
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
            self.source_list.set_focus(line)
            if changed_file:
                self.source_list.set_focus_valign("middle")

    def set_current_line(self, line, source_code_provider):
        """Updates the UI to show the line currently being executed."""

        if self.current_line is not None:
            self.current_line.set_current(False)

        self.show_line(line, source_code_provider)

        line -= 1
        if line >= 0 and line < len(self.source):
            self.current_line = self.source[line]
            self.current_line.set_current(True)

    def update_var_view(self, locals=None, globals=None):
        if locals is None:
            locals = self.debugger.curframe.f_locals
        if globals is None:
            globals = self.debugger.curframe.f_globals

        from pudb.var_view import make_var_view
        self.locals[:] = make_var_view(
                self.get_frame_var_info(read_only=True),
                locals, globals)

    def _get_bp_list(self):
        return [bp
                for fn, bp_lst in self.debugger.get_all_breaks().items()
                for lineno in bp_lst
                for bp in self.debugger.get_breaks(fn, lineno)
                if not bp.temporary]

    def _format_fname(self, fname):
        from os.path import dirname, basename
        name = basename(fname)

        if name == "__init__.py":
            name = "..."+dirname(fname)[-10:]+"/"+name
        return name

    def update_breakpoints(self):
        self.bp_walker[:] = [
                BreakpointFrame(self.debugger.current_bp == (bp.file, bp.line),
                    self._format_fname(bp.file), bp.line)
                for bp in self._get_bp_list()]

    def update_stack(self):
        def make_frame_ui(frame_lineno):
            frame, lineno = frame_lineno

            code = frame.f_code

            class_name = None
            if code.co_argcount and code.co_varnames[0] == "self":
                try:
                    class_name = frame.f_locals["self"].__class__.__name__
                except:
                    pass

            return StackFrame(frame is self.debugger.curframe,
                    code.co_name, class_name,
                    self._format_fname(code.co_filename), lineno)

        frame_uis = [make_frame_ui(fl) for fl in self.debugger.stack]
        if CONFIG["current_stack_frame"] == "top":
            frame_uis = frame_uis[::-1]
        elif CONFIG["current_stack_frame"] == "bottom":
            pass
        else:
            raise ValueError("invalid value for 'current_stack_frame' pref")

        self.stack_walker[:] = frame_uis

    # }}}

# vim: foldmethod=marker:expandtab:softtabstop=4
