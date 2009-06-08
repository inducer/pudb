#! /usr/bin/env python
# -*- coding: utf-8 -*-

import urwid.raw_display
import urwid
import bdb

# TODO: Breakpoint setting and deleting
# TODO: Breakpoint listing
# TODO: File open
# TODO: Stack display 
# TODO: Stack browsing
# TODO: Show stuff when exception happens
# TODO: Postmortem
# TODO: set_trace




HELP_TEXT = """\
Welcome to PuDB, the Python Urwid debugger.
-------------------------------------------

Keys:
    n - next
    s - step
    c - continue
    f - finish

    o - view output

    b - breakpoint

    j/k - up/down
    h/l - scroll left/right
    g/G - start/end

License:
--------

PuDB is licensed to you under the MIT/X Consortium license:

Copyright (c) 2008 Andreas Klöckner

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
    def __init__(self):
        bdb.Bdb.__init__(self)
        self.ui = DebuggerUI(self)

        self.mainpyfile = ''
        self._wait_for_mainpyfile = False

    def reset(self):
        bdb.Bdb.reset(self)
        self.forget()

    def forget(self):
        self.curframe = None

    def interaction(self, frame, traceback):
        self.stack, self.curindex = self.get_stack(frame, traceback)
        self.curframe = self.stack[self.curindex][0]
        self.ui.set_current_line(
                self.curframe.f_code.co_filename, 
                self.curframe.f_lineno)
        self.ui.set_locals(self.curframe.f_locals)
        self.ui.call_with_ui(self.ui.event_loop)

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        if self._wait_for_mainpyfile:
            return
        if self.stop_here(frame):
            #print '--Call--'
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
        #print '--Return--'
        self.interaction(frame, None)

    def user_exception(self, frame, (exc_type, exc_value, exc_traceback)):
        """This function is called if an exception occurs,
        but only if we are to stop at or just below this level."""
        frame.f_locals['__exception__'] = exc_type, exc_value

        if type(exc_type) == type(''):
            exc_type_name = exc_type
        else: 
            exc_type_name = exc_type.__name__

        #print exc_type_name + ':', _saferepr(exc_value)
        self.interaction(frame, exc_traceback)

    def _runscript(self, filename):
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
class SelectableText(urwid.Text):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key




class SignalWrap(urwid.WidgetWrap):
    def __init__(self, w):
        urwid.WidgetWrap.__init__(self, w)
        self.event_listeners = []

    def listen(self, mask, handler):
        self.event_listeners.append((mask, handler))

    def keypress(self, size, key):
        for mask, handler in self.event_listeners:
            if mask is None or mask == key:
                return handler(self, size, key)

        return self._w.keypress(size, key)


class SourceLine(urwid.FlowWidget):
    def __init__(self, dbg_ui, text):
        self.dbg_ui = dbg_ui
        self.text = text
        self.has_breakpoint = False
        self.is_current = False

    def selectable(self):
        return True

    def set_current(self, is_current):
        self.is_current = is_current
        self._invalidate()

    def set_breakpoint(self, has_breakpoint):
        self.has_breakpoint = has_breakpoint
        self._invalidate()

    def rows(self, (maxcol,), focus=False):
        return 1

    def render(self, (maxcol,), focus=False):
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

        text = self.text
        if self.dbg_ui.source_hscroll_start:
            text = text[self.dbg_ui.source_hscroll_start:]

        if len(text) + 2 > maxcol:
            text = text[:maxcol-2]

        line = crnt+bp+text

        if focus:
            attrs.append("focused")

        return urwid.TextCanvas(
                [line], 
                attr=[[(" ".join(attrs+["source"]), maxcol)]],
                maxcol=maxcol) 

    def keypress(self, size, key):
        return key




class DebuggerUI(object):
    def __init__(self, dbg):
        self.debugger = dbg
        Attr = urwid.AttrWrap

        self.source = urwid.SimpleListWalker([])
        self.source_list = urwid.ListBox(self.source)
        self.source_hscroll_start = 0

        self.locals = urwid.SimpleListWalker([])
        self.var_list = urwid.ListBox(self.locals)

        self.stack_walker = urwid.SimpleListWalker(
                [Attr(SelectableText(fname),
                    None, "focused frame")
                    for fname in []])
        self.stack_list = urwid.ListBox(self.stack_walker)

        self.bp_walker = urwid.SimpleListWalker(
                [Attr(SelectableText(fname),
                    None, "focused breakpoint")
                    for fname in []])
        self.bp_list = urwid.ListBox(self.bp_walker)

        rhs_col = urwid.Pile([
            Attr(urwid.Pile([
                ("flow", urwid.Text("Locals:")),
                Attr(self.var_list, "variables"), 
                ]), None, "focused sidebar"),
            Attr(urwid.Pile([
                ("flow", urwid.Text("Stack:")),
                Attr(self.stack_list, "stack"), 
                ]), None, "focused sidebar"),
            Attr(urwid.Pile([
                ("flow", urwid.Text("Breakpoints:")),
                Attr(self.bp_list, "breakpoints"), 
                ]), None, "focused sidebar"),
            ])

        columns = urwid.AttrWrap(
                urwid.Columns(
                    [
                        ("weight", 3, 
                            urwid.AttrWrap(self.source_list, "source")), 
                        ("weight", 1, rhs_col), 
                        ],
                    dividechars=1),
                "background")

        instruct = urwid.Text(u"PuDB - The Python Urwid debugger - F1 for help"
                u" - © Andreas Klöckner 2008")
        header = urwid.AttrWrap(instruct, "header")
        self.top = SignalWrap(urwid.Frame(columns, header))

        # listeners -----------------------------------------------------------
        def end():
            self.quit_event_loop = True

        def next(w, size, key):
            self.debugger.set_next(self.debugger.curframe)
            end()

        def step(w, size, key):
            self.debugger.set_step()
            end()

        def show_output(w, size, key):
            self.screen.stop()
            raw_input("Hit Enter to return:")
            self.screen.start()

        def finish(w, size, key):
            self.debugger.set_return(self.debugger.curframe)
            end()


        def cont(w, size, key):
            self.debugger.set_continue()
            end()

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

        def breakpoint(w, size, key):
            if self.shown_file:
                sline, pos = self.source.get_focus()
                err = self.debugger.set_break(self.shown_file, pos+1, 
                        temporary=False, cond=None, funcname=None)
                sline.set_breakpoint(True)
                self.update_breakpoints()
            else:
                raise RuntimeError, "no valid current file"

        def quit(w, size, key):
            self.debugger.set_quit()
            end()

        def help(w, size, key):
            l = urwid.ListBox([urwid.Text(HELP_TEXT)])
            ok = Attr(urwid.Button("OK", lambda btn: end()), "button")
            w = urwid.Columns([
                l, 
                ("fixed", 10, urwid.ListBox([ok])),
                ])
            #w = urwid.Padding(w, ('fixed left', 1), ('fixed right', 0))
            w = urwid.LineBox(w)

            w = urwid.Overlay(w, self.top,
                    align="center",
                    valign="middle",
                    width=('relative', 75),
                    height=('relative', 75),
                    )
            w = Attr(w, "background")

            self.event_loop(w)

        self.top.listen("n", next)
        self.top.listen("s", step)
        self.top.listen("o", show_output)
        self.top.listen("f", finish)
        self.top.listen("c", cont)

        self.top.listen("o", show_output)

        self.top.listen("j", move_down)
        self.top.listen("k", move_up)
        self.top.listen("h", scroll_left)
        self.top.listen("l", scroll_right)

        self.top.listen("home", move_home)
        self.top.listen("end", move_end)
        self.top.listen("g", move_home)
        self.top.listen("G", move_end)

        self.top.listen("b", breakpoint)

        self.top.listen("q", quit)
        self.top.listen("H", help)
        self.top.listen("f1", help)

        # setup ---------------------------------------------------------------
        self.screen = urwid.raw_display.Screen()
        self.setup_palette(self.screen)

        self.show_count = 0
        self.shown_file = None

        self.current_line = None

        self.quit_event_loop = False

    @staticmethod
    def setup_palette(screen):
        screen.register_palette([
            ("header", "black", "dark cyan", "standout"),

            ("source", "yellow", "dark blue", "standout"),
            ("focused source", "black", "dark green"),
            ("current source", "black", "dark cyan"),
            ("current focused source", "white", "dark cyan"),

            ("breakpoint source", "yellow", "dark red", "standout"),
            ("breakpoint focused source", "black", "dark red"),
            ("current breakpoint source", "black", "dark red"),
            ("current breakpoint focused source", "white", "dark red"),

            ("variables", "black", "dark cyan", "standout"),
            ("focused variable", "black", "dark green", "standout"),

            ("stack", "black", "dark cyan", "standout"),
            ("focused frame", "black", "dark green", "standout"),

            ("breakpoint", "black", "dark cyan", "standout"),
            ("focused breakpoint", "black", "dark green", "standout"),

            ("button", "white", "dark blue", "standout"),

            ("background", "black", "light gray", "standout"),
            ("focused sidebar", "yellow", "dark gray", "standout"),
            ])
    
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
        finally:
            self.quit_event_loop = prev_quit_loop

    # debugger-facing interface -----------------------------------------------
    def set_current_file(self, fname):
        if self.shown_file != fname:
            try:
                inf = open(fname)
            except IOError:
                self.source[:] = [SourceLine(self, fname)]
            else:
                self.source[:] = [
                        SourceLine(self, line.rstrip("\n"))
                        for line in inf.readlines()]
            self.shown_file = fname

            self.current_line = None

    def set_current_line(self, fname, line):
        self.set_current_file(fname)

        line = line-1
        if self.current_line is not None:
            self.current_line.set_current(False)

        if line >= 0 and line < len(self.source):
            self.current_line = self.source[line]
            self.current_line.set_current(True)
            self.source.set_focus(line)
            #self.source_list.shi('middle')

    def set_locals(self, locals):
        vars = locals.keys()
        vars.sort()

        self.locals[:] = [
                urwid.AttrWrap(
                    SelectableText("%s: %s" % (var, locals[var])), 
                    None, "focused variable")
                for var in vars
                if not var.startswith("_")]

    def update_breakpoints(self):
        self.bp_walker[:] = [
                urwid.AttrWrap(
                    SelectableText(str(bp)),
                    "breakpoint", "focused breakpoint")
                for bp in self.debugger.get_all_breaks()]




def main():
    import sys
    if not sys.argv[1:]:
        print "usage: %s scriptfile [arg] ..." % sys.argv[0]
        sys.exit(2)

    mainpyfile =  sys.argv[1]
    from os.path import exists, dirname
    if not exists(mainpyfile):
        print 'Error:', mainpyfile, 'does not exist'
        sys.exit(1)

    # Hide "pdb.py" from argument list
    del sys.argv[0]         

    # Replace pdb's dir with script's dir in front of module search path.
    sys.path[0] = dirname(mainpyfile)

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user from the command line. The best approach would be to
    # have a "restart" command which would allow explicit specification of
    # command line arguments.

    dbg = Debugger()
    dbg._runscript(mainpyfile)




if __name__=='__main__':
    main()
