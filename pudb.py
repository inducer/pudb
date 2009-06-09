#! /usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import urwid.curses_display as display
except ImportError:
    import urwid.raw_display as display

import urwid
import bdb
from code import InteractiveConsole

try:
    import readline
    import rlcompleter
    HAVE_READLINE = True
except ImportError:
    HAVE_READLINE = False

# TODO: Pop open local variables




HELP_TEXT = """\
Welcome to PuDB, the Python Urwid debugger.
-------------------------------------------

Keys:
    n - step over ("next")
    s - step into
    c - continue
    r/f - finish current function
    t - run to cursor
    e - re-show traceback [post-mortem mode]

    ! - invoke python shell in current environment

    b - toggle breakpoint
    m - open module

    j/k - up/down
    h/l - scroll left/right
    g/G - start/end
    / - search
    ,/. - search next/previous

    V - focus variables
    S - focus stack
    B - focus breakpoint list

    f1/?/H - show this help screen

License:
--------

PuDB is licensed to you under the MIT/X Consortium license:

Copyright (c) 2009 Andreas Klöckner

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



# debugger interface ----------------------------------------------------------
class Debugger(bdb.Bdb):
    def __init__(self, steal_output=False):
        bdb.Bdb.__init__(self)
        self.ui = DebuggerUI(self)
        self.steal_output = steal_output

        self.mainpyfile = ''
        self._wait_for_mainpyfile = False

        self.ignore_stack_start = 0
        self.post_mortem = False

        if steal_output:
            raise NotImplementedError("output stealing")
            import sys
            from cStringIO import StringIO
            self.stolen_output = sys.stderr = sys.stdout = StringIO()
            sys.stdin = StringIO("") # avoid spurious hangs

    def enter_post_mortem(self, exc_tuple):
        self.post_mortem = True
        self.ui.enter_post_mortem(exc_tuple)

    def reset(self):
        bdb.Bdb.reset(self)
        self.forget()

    def forget(self):
        self.curframe = None

    def do_clear(self, arg):
        self.clear_bpbynumber(int(arg))

    def set_frame_index(self, index):
        self.curindex = index
        self.curframe, lineno = self.stack[index]
        self.ui.set_current_line(self.curframe.f_code.co_filename, lineno)
        self.ui.set_locals(self.curframe.f_locals)
        self.ui.update_stack()

    def interaction(self, frame, traceback, exc_type=None, exc_value=None):
        self.stack, self.curindex = self.get_stack(frame, traceback)
        if traceback is not None:
            self.curindex = len(self.stack)-1

        if traceback:
            self.ui.call_with_ui(
                    self.ui.show_exception, 
                    exc_type, exc_value, traceback)

        self.set_frame_index(self.curindex)

        self.ui.call_with_ui(self.ui.event_loop)

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        if self._wait_for_mainpyfile:
            return
        if self.stop_here(frame):
            self.interaction(frame, None)

    def user_line(self, frame):
        """This function is called when we stop or break at this line."""
        if self._wait_for_mainpyfile:
            if (self.mainpyfile != self.canonic(frame.f_code.co_filename)
                or frame.f_lineno<= 0):
                return
            self._wait_for_mainpyfile = False
        self.interaction(frame, None)

    def user_return(self, frame, return_value):
        """This function is called when a return trap is set here."""
        frame.f_locals['__return__'] = return_value
        self.interaction(frame, None)

    def user_exception(self, frame, (exc_type, exc_value, exc_traceback)):
        """This function is called if an exception occurs,
        but only if we are to stop at or just below this level."""
        frame.f_locals['__exception__'] = exc_type, exc_value
        self.enter_post_mortem((exc_type, exc_value, exc_traceback))

        self.interaction(frame, exc_traceback, exc_type, exc_value)

    def _runscript(self, filename):
        self.ignore_stack_start = 2

        # Start with fresh empty copy of globals and locals and tell the script
        # that it's being run as __main__ to avoid scripts being able to access
        # the debugger's namespace.
        globals_ = {"__name__" : "__main__"}
        locals_ = globals_

        # When bdb sets tracing, a number of call and line events happens
        # BEFORE debugger even reaches user's code (and the exact sequence of
        # events depends on python version). So we take special measures to
        # avoid stopping before we reach the main script (see user_line and
        # user_call for details).
        self._wait_for_mainpyfile = 1
        self.mainpyfile = self.canonic(filename)
        statement = 'execfile( "%s")' % filename
        self.run(statement, globals=globals_, locals=locals_)





# UI stuff --------------------------------------------------------------------
class MyConsole(InteractiveConsole):
    def __init__(self, locals):
        InteractiveConsole.__init__(self, locals)

        if HAVE_READLINE:
            import os
            import atexit

            histfile = os.path.join(os.environ["HOME"], ".pudbhist")
            if os.access(histfile, os.R_OK):
                readline.read_history_file(histfile)
            atexit.register(readline.write_history_file, histfile)
            readline.parse_and_bind("tab: complete")





class SelectableText(urwid.Text):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key



def make_hotkey_markup(s):
    import re
    match = re.match(r"^([^_]*)_(.)(.*)$", s)
    assert match is not None

    return [
            (None, match.group(1)),
            ("hotkey", match.group(2)),
            (None, match.group(3)),
            ]





class SignalWrap(urwid.WidgetWrap):
    def __init__(self, w):
        urwid.WidgetWrap.__init__(self, w)
        self.event_listeners = []

    def listen(self, mask, handler):
        self.event_listeners.append((mask, handler))

    def keypress(self, size, key):
        result = self._w.keypress(size, key)

        if result is not None:
            for mask, handler in self.event_listeners:
                if mask is None or mask == key:
                    return handler(self, size, key)

        return result




class SourceLine(urwid.FlowWidget):
    def __init__(self, dbg_ui, text, attr=None):
        self.dbg_ui = dbg_ui
        self.text = text
        self.attr = attr
        self.has_breakpoint = False
        self.is_current = False
        self.highlight = False

    def selectable(self):
        return True

    def set_current(self, is_current):
        self.is_current = is_current
        self._invalidate()

    def set_highlight(self, highlight):
        self.highlight = highlight
        self._invalidate()

    def set_breakpoint(self, has_breakpoint):
        self.has_breakpoint = has_breakpoint
        self._invalidate()

    def rows(self, (maxcol,), focus=False):
        return 1

    def render(self, (maxcol,), focus=False):
        hscroll = self.dbg_ui.source_hscroll_start
        attrs = []
        if self.is_current:
            crnt = ">"
            attrs.append("current")
        else:
            crnt = " "

        if self.has_breakpoint:
            bp = "*"
            attrs.append("breakpoint")
        else:
            bp = " "

        if focus:
            attrs.append("focused")
        elif self.highlight:
            attrs.append("highlighted")

        if not attrs and self.attr is not None:
            attr = self.attr
        else:
            attr = [(" ".join(attrs+["source"]), hscroll+maxcol-2)]

        from urwid.util import rle_subseg, rle_len

        text = self.text
        if self.dbg_ui.source_hscroll_start:
            text = text[hscroll:]
            attr = rle_subseg(attr, 
                    self.dbg_ui.source_hscroll_start, 
                    rle_len(attr))

        text = crnt+bp+text
        attr = [("source", 2)] + attr

        # clipping ------------------------------------------------------------
        if len(text) > maxcol:
            text = text[:maxcol]
            attr = rle_subseg(attr, 0, maxcol)

        # shipout -------------------------------------------------------------
        from urwid.util import apply_target_encoding
        txt, cs = apply_target_encoding(text)

        return urwid.TextCanvas([txt], [attr], [cs], maxcol=maxcol) 

    def keypress(self, size, key):
        return key





class SearchBox(urwid.Edit):
    def __init__(self, ui):
        self.ui = ui
        urwid.Edit.__init__(self,
                [("label", "Search: ") ], 
                self.ui.last_search or "")
        self.highlight_line = None

        _, self.search_start = self.ui.source.get_focus()

    def keypress(self, size, key):
        result = urwid.Edit.keypress(self, size, key)

        if result is not None:
            if key == "esc":
                self.cancel_search()
                return None
            elif key == "enter":
                if self.get_edit_text():
                    self.ui.lhs_col.set_focus(self.ui.lhs_col.widget_list[1])
                else:
                    self.cancel_search()
                return None
        else:
            if self.do_search(1, self.search_start):
                self.ui.search_attrwrap.set_attr("value")
            else:
                self.ui.search_attrwrap.set_attr("invalid value")

        return result

    def cancel_highlight(self):
        if self.highlight_line is not None:
            self.highlight_line.set_highlight(False)
            self.highlight_line = None

    def do_search(self, dir, start=None):
        self.cancel_highlight()

        if start is None:
            _, start = self.ui.source.get_focus()
        s = self.ui.search_box.get_edit_text()

        case_insensitive = s.lower() == s

        i = start+dir
        while i != start:
            sline = self.ui.source[i].text
            if case_insensitive:
                sline = sline.lower()

            if s in sline:
                sl = self.ui.source[i]
                sl.set_highlight(True)
                self.highlight_line = sl
                self.ui.source.set_focus(i)
                return True

            last_i = i
            i = (i+dir) % len(self.ui.source)

        return False

    def cancel_search(self):
        self.cancel_highlight()

        self.ui.search_box = None
        del self.ui.lhs_col.item_types[0]
        del self.ui.lhs_col.widget_list[0]
        self.ui.lhs_col.set_focus(self.ui.lhs_col.widget_list[0])




class DebuggerUI(object):
    CAPTION_TEXT = (u"PuDB - The Python Urwid debugger - F1 for help"
            u" - © Andreas Klöckner 2009")

    def __init__(self, dbg):
        self.debugger = dbg
        Attr = urwid.AttrWrap

        self.search_box = None
        self.last_search = None

        self.source = urwid.SimpleListWalker([])
        self.source_list = urwid.ListBox(self.source)
        self.source_hscroll_start = 0

        self.lhs_col = urwid.Pile([
            ("weight", 1, urwid.AttrWrap(self.source_list, "source"))
            ])

        self.locals = urwid.SimpleListWalker([])
        self.var_list = urwid.ListBox(self.locals)

        self.stack_walker = urwid.SimpleListWalker(
                [Attr(SelectableText(fname, wrap="clip"),
                    None, "focused frame")
                    for fname in []])
        self.stack_list = SignalWrap(
                urwid.ListBox(self.stack_walker))

        self.bp_walker = urwid.SimpleListWalker(
                [Attr(SelectableText(fname, wrap="clip"),
                    None, "focused breakpoint")
                    for fname in []])
        self.bp_list = SignalWrap(
                urwid.ListBox(self.bp_walker))

        self.rhs_col = urwid.Pile([
            Attr(urwid.Pile([
                ("flow", urwid.Text(make_hotkey_markup("_Variables:"))),
                Attr(self.var_list, "variables"), 
                ]), None, "focused sidebar"),
            Attr(urwid.Pile([
                ("flow", urwid.Text(make_hotkey_markup("_Stack:"))),
                Attr(self.stack_list, "stack"), 
                ]), None, "focused sidebar"),
            Attr(urwid.Pile([
                ("flow", urwid.Text(make_hotkey_markup("_Breakpoints:"))),
                Attr(self.bp_list, "breakpoint"), 
                ]), None, "focused sidebar"),
            ])

        self.columns = urwid.AttrWrap(
                urwid.Columns(
                    [
                        ("weight", 3, self.lhs_col), 
                        ("weight", 1, self.rhs_col), 
                        ],
                    dividechars=1),
                "background")

        self.caption = urwid.Text(self.CAPTION_TEXT)
        header = urwid.AttrWrap(self.caption, "header")
        self.top = SignalWrap(urwid.Frame(self.columns, header))

        # stack listeners -----------------------------------------------------
        def examine_frame(w, size, key):
            _, pos = self.stack_list._w.get_focus()
            self.debugger.set_frame_index(
                    self.debugger.ignore_stack_start + pos)

        self.stack_list.listen("enter", examine_frame)

        # stack listeners -----------------------------------------------------
        def examine_breakpoint(w, size, key):
            _, pos = self.bp_list._w.get_focus()
            bp = self._get_bp_list()[pos]

            def make_lv(label, value):
                return urwid.AttrWrap(urwid.Text([
                    ("label", label), str(value)]),
                    "fixed value", "fixed value")
        
            if bp.cond is None:
                cond = ""
            else:
                cond = str(bp.cond)

            enabled_checkbox = urwid.CheckBox(
                    "Enabled", bp.enabled)
            cond_edit = urwid.Edit([
                ("label", "Condition: ")
                ], cond)

            lb = urwid.ListBox([
                make_lv("File: ", bp.file),
                make_lv("Line: ", bp.line),
                make_lv("Hits: ", bp.hits),
                enabled_checkbox,
                urwid.AttrWrap(cond_edit, "value", "value")
                ])

            if self.dialog(lb, [
                ("OK", True),
                ("Cancel", False),
                ], title="Edit Breakpoint"):
                bp.enabled = enabled_checkbox.get_state()
                cond = cond_edit.get_edit_text()
                if cond:
                    bp.cond = cond
                else:
                    bp.cond = None

        self.bp_list.listen("enter", examine_breakpoint)

        # top-level listeners -------------------------------------------------
        def end():
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
                canon_file = self.debugger.canonic(self.shown_file)
                lineno = pos+1

                err = self.debugger.set_break(self.shown_file, pos+1, temporary=True)
                if err:
                    self.message("Error dealing with breakpoint:\n"+ err)

                self.debugger.set_continue()
                end()

        def show_traceback(w, size, key):
            if self.debugger.post_mortem:
                self.show_exception(*self.post_mortem_exc_tuple)
            else:
                self.message("Not in post-mortem mode: No traceback available.")

        def show_output(w, size, key):
            self.screen.stop()
            raw_input("Hit Enter to return:")
            self.screen.start()

        def run_shell(w, size, key):
            self.screen.stop()

            if not hasattr(self, "shell_ret_message_shown"):
                banner = "Hit Ctrl-D to return to PuDB."
                self.shell_ret_message_shown = True
            else:
                banner = ""

            curframe = self.debugger.curframe
            loc = curframe.f_locals.copy()
            loc.update(curframe.f_globals)

            cons = MyConsole(loc)
            cons.interact(banner)
            self.screen.start()

        class RHColumnFocuser:
            def __init__(self, idx):
                self.idx = idx

            def __call__(subself, w, size, key):
                self.columns.set_focus(self.rhs_col)
                self.rhs_col.set_focus(self.rhs_col.widget_list[subself.idx])

        def move_home(w, size, key):
            self.source.set_focus(0)

        def move_end(w, size, key):
            self.source.set_focus(len(self.source))

        def move_down(w, size, key):
            w.keypress(size, "down")

        def move_up(w, size, key):
            w.keypress(size, "up")

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
            if self.search_box is None:
                _, search_start = self.source.get_focus()

                self.search_box = SearchBox(self)
                self.search_attrwrap = urwid.AttrWrap(self.search_box, "value")

                self.lhs_col.item_types.insert(
                        0, ("flow", None))
                self.lhs_col.widget_list.insert( 0, self.search_attrwrap)

                self.columns.set_focus(self.lhs_col)
                self.lhs_col.set_focus(self.search_attrwrap)
            else:
                self.columns.set_focus(self.lhs_col)
                self.lhs_col.set_focus(self.search_attrwrap)

        def search_next(w, size, key):
            if self.search_box is not None:
                self.search_box.do_search(1)
            else:
                self.message("No previous search term.")

        def search_previous(w, size, key):
            if self.search_box is not None:
                self.search_box.do_search(-1)
            else:
                self.message("No previous search term.")

        def toggle_breakpoint(w, size, key):
            if self.shown_file:
                sline, pos = self.source.get_focus()
                canon_file = self.debugger.canonic(self.shown_file)
                lineno = pos+1

                existing_breaks = self.debugger.get_breaks(canon_file, lineno)
                if existing_breaks:
                    err = self.debugger.clear_break(canon_file, lineno)
                    sline.set_breakpoint(False)
                else:
                    err = self.debugger.set_break(self.shown_file, pos+1)
                    sline.set_breakpoint(True)

                if err:
                    self.message("Error dealing with breakpoint:\n"+ err)

                self.update_breakpoints()
            else:
                raise RuntimeError, "no valid current file"

        def pick_module(w, size, key):
            from os.path import splitext

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

            import sys
            modules = sorted(name
                    for name, mod in sys.modules.iteritems()
                    if mod_exists(mod))

            def build_filtered_mod_list(filt_string=""):
                return [urwid.AttrWrap(SelectableText(mod),
                        None, "focused selectable")
                        for mod in modules if filt_string in mod]

            mod_list = urwid.SimpleListWalker(build_filtered_mod_list())
            lb = urwid.ListBox(mod_list)

            class FilterEdit(urwid.Edit):
                def keypress(self, size, key):
                    result = urwid.Edit.keypress(self, size, key)

                    if result is None:
                        mod_list[:] = build_filtered_mod_list(
                                self.get_edit_text())

                    return result

            edit = FilterEdit([("label", "Filter: ")])
            w = urwid.Pile([
                ("flow", urwid.AttrWrap(edit, "value")),
                ("fixed", 1, urwid.SolidFill()),
                urwid.AttrWrap(lb, "selectable")])

            result = self.dialog(w, [
                ("OK", True),
                ("Cancel", False),
                ], title="Pick Module")

            if result:
                widget, pos = lb.get_focus()
                mod = sys.modules[widget.get_text()[0]]
                filename = self.debugger.canonic(mod.__file__)

                base, ext = splitext(filename)
                if ext == ".pyc":
                    ext = ".py"
                    filename = base+".py"

                self.set_current_file(filename)

        def quit(w, size, key):
            self.debugger.set_quit()
            end()

        def help(w, size, key):
            self.message(HELP_TEXT, title="PuDB Help")

        self.top.listen("n", next)
        self.top.listen("s", step)
        self.top.listen("f", finish)
        self.top.listen("r", finish)
        self.top.listen("c", cont)
        self.top.listen("t", run_to_cursor)
        self.top.listen("e", show_traceback)

        self.top.listen("o", show_output)
        self.top.listen("!", run_shell)

        self.top.listen("j", move_down)
        self.top.listen("k", move_up)
        self.top.listen("h", scroll_left)
        self.top.listen("l", scroll_right)

        self.top.listen("/", search)
        self.top.listen(",", search_previous)
        self.top.listen(".", search_next)

        self.top.listen("V", RHColumnFocuser(0))
        self.top.listen("S", RHColumnFocuser(1))
        self.top.listen("B", RHColumnFocuser(2))

        self.top.listen("home", move_home)
        self.top.listen("end", move_end)
        self.top.listen("g", move_home)
        self.top.listen("G", move_end)

        self.top.listen("b", toggle_breakpoint)
        self.top.listen("m", pick_module)

        self.top.listen("q", quit)
        self.top.listen("H", help)
        self.top.listen("f1", help)
        self.top.listen("?", help)

        # setup ---------------------------------------------------------------
        self.screen = display.Screen()
        self.setup_palette(self.screen)

        self.show_count = 0
        self.shown_file = None

        self.current_line = None

        self.quit_event_loop = False

    def message(self, msg, title="Message", **kwargs):
        self.dialog(
                urwid.ListBox([urwid.Text(msg)]),
                [("OK", True)], title=title, **kwargs)

    def dialog(self, content, buttons_and_results, 
            title=None, bind_enter_esc=True):
        class ResultSetter:
            def __init__(subself, res):
                subself.res = res

            def __call__(subself, btn):
                self.quit_event_loop = [subself.res]
            
        Attr = urwid.AttrWrap

        if bind_enter_esc:
            content = SignalWrap(content)
            def enter(w, size, key): self.quit_event_loop = [True]
            def esc(w, size, key): self.quit_event_loop = [False]
            content.listen("enter", enter)
            content.listen("esc", esc)

        w = urwid.Columns([
            content, 
            ("fixed", 1, urwid.SolidFill()),
            ("fixed", 10, urwid.ListBox([
                Attr(urwid.Button(btn_text, ResultSetter(btn_result)), 
                    "button", "focused button")
                for btn_text, btn_result in buttons_and_results
                ])),
            ])

        if title is not None:
            w = urwid.Pile([
                ("flow", urwid.AttrWrap(
                    urwid.Text(title, align="center"), 
                    "dialog title")),
                ("fixed", 1, urwid.SolidFill()),
                w])

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

        if hasattr(urwid.escape, "_fg_attr_xterm"):
            def add_setting(color, setting):
                return color
        else:
            def add_setting(color, setting):
                return color+","+setting

        palette = [
            ("header", "black", "light gray", "standout"),

            ("breakpoint source", "yellow", "dark red"),
            ("breakpoint focused source", "black", "dark red"),
            ("current breakpoint source", "black", "dark red"),
            ("current breakpoint focused source", "white", "dark red"),

            ("variables", "black", "dark cyan"),
            ("focused variable", "black", "dark green"),
            ("return value", "yellow", "dark blue"),
            ("focused return value", "white", "dark blue"),

            ("stack", "black", "dark cyan", "standout"),
            ("focused frame", "black", "dark green"),
            ("current frame", add_setting("white", "bold"), 
                "dark cyan"),
            ("focused current frame", add_setting("white", "bold"), 
                "dark green", "bold"),

            ("breakpoint", "black", "dark cyan"),
            ("focused breakpoint", "black", "dark green"),

            ("selectable", "black", "dark cyan"),
            ("focused selectable", "black", "dark green"),

            ("button", "white", "dark blue"),
            ("focused button", "light cyan", "black"),

            ("background", "black", "light gray"),
            ("hotkey", add_setting("black", "underline"), "light gray", "underline"),
            ("focused sidebar", "yellow", "light gray", "standout"),

            ("warning", add_setting("white", "bold"), "dark red", "standout"),

            ("label", "black", "light gray"),
            ("value", "black", "dark cyan"),
            ("fixed value", "dark gray", "dark cyan"),
            ("invalid value", "light red", "dark cyan"),

            ("dialog title", add_setting("white", "bold"), "dark cyan"),

            # highlighting
            ("source", "yellow", "dark blue"),
            ("focused source", "black", "dark green"),
            ("highlighted source", "black", "dark magenta"),
            ("current source", "black", "dark cyan"),
            ("current focused source", "white", "dark cyan"),
            ("current highlighted source", "white", "dark cyan"),

            ("keyword", add_setting("white", "bold"), "dark blue"),
            ("literal", "light magenta", "dark blue"),
            ("punctuation", "light gray", "dark blue"),
            ("comment", "light gray", "dark blue"),
            ]
        screen.register_palette(palette)
    
    # UI enter/exit -----------------------------------------------------------
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
            f(*args, **kwargs)
        finally:
            self.hide()

    # interaction -------------------------------------------------------------
    def event_loop(self, toplevel=None):
        prev_quit_loop = self.quit_event_loop

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

    # debugger-facing interface -----------------------------------------------
    def enter_post_mortem(self, exc_tuple):
        self.post_mortem_exc_tuple = exc_tuple

        self.caption.set_text([
                (None, self.CAPTION_TEXT+ " "),

                ("warning", "[POST-MORTEM MODE]")
                ])

    def format_source(self, lines):
        try:
            import pygments
        except ImportError:
            return [SourceLine(self, 
                line.rstrip("\n\r").replace("\t", 8*" "), None)
                for line in lines]
        else:
            from pygments import highlight
            from pygments.lexers import PythonLexer
            from pygments.formatter import Formatter
            import pygments.token as t

            result = []

            ATTR_MAP = {
                    t.Token: "source",
                    t.Keyword: "keyword",
                    t.Literal: "literal",
                    t.Punctuation: "punctuation",
                    t.Comment: "comment",
                    }

            class UrwidFormatter(Formatter):
                def __init__(subself, **options):
                    Formatter.__init__(subself, **options)
                    subself.current_line = ""
                    subself.current_attr = []

                def format(subself, tokensource, outfile):
                    def add_snippet(ttype, s):
                        if not s:
                            return 

                        while not ttype in ATTR_MAP:
                            if ttype.parent is not None:
                                ttype = ttype.parent
                            else:
                                raise RuntimeError(
                                        "untreated token type: %s" % str(ttype))

                        attr = ATTR_MAP[ttype]

                        subself.current_line += s
                        subself.current_attr.append((attr, len(s)))

                    def shipout_line():
                        result.append(
                                SourceLine(self, 
                                    subself.current_line,
                                    subself.current_attr))
                        subself.current_line = ""
                        subself.current_attr = []

                    for ttype, value in tokensource:
                        while True:
                            newline_pos = value.find("\n")
                            if newline_pos == -1:
                                add_snippet(ttype, value)
                                break
                            else:
                                add_snippet(ttype, value[:newline_pos])
                                shipout_line()
                                value = value[newline_pos+1:]

                    if subself.current_line:
                        shipout_line()

            highlight("".join(l.replace("\t", 8*" ") for l in lines), 
                    PythonLexer(), UrwidFormatter())

            return result

    def set_current_file(self, fname):
        if self.shown_file != fname:
            try:
                inf = open(fname, "r")
                self.source[:] = self.format_source(inf.readlines())
                inf.close()
            except:
                from traceback import format_exception
                import sys

                self.message("Trouble loading '%s':\n\n%s" % (
                    fname, "".join(format_exception(*sys.exc_info()))))
                self.source[:] = [SourceLine(self, 
                    "Error while loading '%s'." % fname)]

            self.shown_file = fname
            self.current_line = None

    def set_current_line(self, fname, line):
        changed_file =  self.shown_file != fname

        self.set_current_file(fname)

        line = line-1
        if self.current_line is not None:
            self.current_line.set_current(False)

        if line >= 0 and line < len(self.source):
            self.current_line = self.source[line]
            self.current_line.set_current(True)
            self.source_list.set_focus(line)
            if changed_file:
                self.source_list.set_focus_valign("middle")

    def set_locals(self, locals):
        vars = locals.keys()
        vars.sort()

        loc_list = []

        def format_value(v):
            try:
                return str(v)
            except:
                return "*** ERROR in str() ***"

        if "__return__" in vars:
            loc_list.append(
                    urwid.AttrWrap(
                        SelectableText("Return: %s" % format_value(locals["__return__"]),
                            wrap="clip"), 
                        "return value", "focused return value"))

        loc_list.extend(
                urwid.AttrWrap(
                    SelectableText("%s: %s" % (var, format_value(locals[var])),
                        wrap="clip"), 
                    None, "focused variable")
                for var in vars
                if not var.startswith("_"))


        self.locals[:] = loc_list

    def _get_bp_list(self):
        return [bp
                for fn, bp_lst in self.debugger.get_all_breaks().iteritems()
                for lineno in bp_lst
                for bp in self.debugger.get_breaks(fn, lineno)
                if not bp.temporary]

    def _format_fname(self, fname):
        from os.path import dirname, basename
        name = basename(fname)

        if name == "__init__.py":
            name = "..."+dirname(filename)[:-10]+name
        return name

    def update_breakpoints(self):
        def format_bp(bp):
            return "%s:%d" % (self._format_fname(bp.file), bp.line)

        self.bp_walker[:] = [
                urwid.AttrWrap(
                    SelectableText(format_bp(bp), wrap="clip"),
                    None, "focused breakpoint")
                for bp in self._get_bp_list()]

    def update_stack(self):
        def format_frame(frame_lineno):
            frame, lineno = frame_lineno
            code = frame.f_code
            result = "%s (%s:%d)" % (
                    code.co_name,
                    self._format_fname(code.co_filename), 
                    lineno)

            if frame is self.debugger.curframe:
                result = ">> "+result
                attr = "current frame"
                focused_attr = "focused current frame"
            else:
                result = "   "+result
                attr = None
                focused_attr = "focused frame"

            return urwid.AttrWrap(SelectableText(result, wrap="clip"),
                    attr, focused_attr)


        self.stack_walker[:] = [format_frame(frame)
                for frame in self.debugger.stack[self.debugger.ignore_stack_start:]]

    def show_exception(self, exc_type, exc_value, traceback):
        from traceback import format_exception

        self.message(
                "".join(format_exception(
                    exc_type, exc_value, traceback)),
                title="Exception Occurred")



def set_trace():
    import sys
    Debugger().set_trace(sys._getframe().f_back)

def post_mortem(t):
    p = Pdb()
    p.reset()
    while t.tb_next is not None:
        t = t.tb_next
    p.interaction(t.tb_frame, t)

def pm():
    import sys
    post_mortem(sys.last_traceback)

def main():
    import sys
    if not sys.argv[1:]:
        print "usage: %s scriptfile [-s] [arg] ..." % sys.argv[0]
        sys.exit(2)

    mainpyfile =  sys.argv[1]
    from os.path import exists, dirname
    if not exists(mainpyfile):
        print 'Error:', mainpyfile, 'does not exist'
        sys.exit(1)

    # Hide "pudb.py" from argument list
    del sys.argv[0]

    steal_output = sys.argv[0] == "-s"
    if steal_output:
        del sys.argv[0]

    # Replace pdb's dir with script's dir in front of module search path.
    sys.path[0] = dirname(mainpyfile)

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user from the command line. The best approach would be to
    # have a "restart" command which would allow explicit specification of
    # command line arguments.

    dbg = Debugger(steal_output=steal_output)
    try:
        dbg._runscript(mainpyfile)
    except:
        exc_tuple = sys.exc_info()
        type, value, tb = exc_tuple
        dbg.enter_post_mortem(exc_tuple)
        dbg.interaction(tb.tb_frame, tb, type, value)




if __name__=='__main__':
    main()
