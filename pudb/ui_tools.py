from __future__ import absolute_import, division, print_function
import urwid
from urwid.util import _target_encoding, calc_width, calc_text_pos


# generic urwid helpers -------------------------------------------------------

def text_width(txt):
    """
    Return the width of the text in the terminal

    Use this instead of len() whenever txt could contain double- or zero-width
    Unicode characters.

    """
    return calc_width(txt, 0, len(txt))


def make_canvas(txt, attr, maxcol, fill_attr=None):
    processed_txt = []
    processed_attr = []
    processed_cs = []

    for line, line_attr in zip(txt, attr):
        # filter out zero-length attrs
        line_attr = [(aname, l) for aname, l in line_attr if l > 0]

        diff = maxcol - text_width(line)
        if diff > 0:
            line += " "*diff
            line_attr.append((fill_attr, diff))
        else:
            from urwid.util import rle_subseg
            line = line[:calc_text_pos(line, 0, len(line), maxcol)[0]]
            line_attr = rle_subseg(line_attr, 0, maxcol)

        from urwid.util import apply_target_encoding
        encoded_line, line_cs = apply_target_encoding(line)

        # line_cs contains byte counts as requested by TextCanvas, but
        # line_attr still contains column counts at this point: let's fix this.
        def get_byte_line_attr(line, line_attr):
            i = 0
            for label, column_count in line_attr:
                byte_count = len(line[i:i+column_count].encode(_target_encoding))
                i += column_count
                yield label, byte_count

        line_attr = list(get_byte_line_attr(line, line_attr))

        processed_txt.append(encoded_line)
        processed_attr.append(line_attr)
        processed_cs.append(line_cs)

    return urwid.TextCanvas(
            processed_txt,
            processed_attr,
            processed_cs,
            maxcol=maxcol)


def make_hotkey_markup(s):
    import re
    match = re.match(r"^([^_]*)_(.)(.*)$", s)
    assert match is not None

    return [
            (None, match.group(1)),
            ("hotkey", match.group(2)),
            (None, match.group(3)),
            ]


def labelled_value(label, value):
    return urwid.AttrMap(urwid.Text([
        ("label", label), str(value)]),
        "fixed value", "fixed value")


class SelectableText(urwid.Text):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class SignalWrap(urwid.WidgetWrap):
    def __init__(self, w, is_preemptive=False):
        urwid.WidgetWrap.__init__(self, w)
        self.event_listeners = []
        self.is_preemptive = is_preemptive

    def listen(self, mask, handler):
        self.event_listeners.append((mask, handler))

    def keypress(self, size, key):
        result = key

        if self.is_preemptive:
            for mask, handler in self.event_listeners:
                if mask is None or mask == key:
                    result = handler(self, size, key)
                    break

        if result is not None:
            result = self._w.keypress(size, key)

        if result is not None and not self.is_preemptive:
            for mask, handler in self.event_listeners:
                if mask is None or mask == key:
                    return handler(self, size, key)

        return result


# {{{ debugger-specific stuff

class StackFrame(urwid.FlowWidget):
    def __init__(self, is_current, name, class_name, filename, line):
        self.is_current = is_current
        self.name = name
        self.class_name = class_name
        self.filename = filename
        self.line = line

    def selectable(self):
        return True

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        maxcol = size[0]
        if focus:
            apfx = "focused "
        else:
            apfx = ""

        if self.is_current:
            apfx += "current "
            crnt_pfx = ">> "
        else:
            crnt_pfx = "   "

        text = crnt_pfx+self.name
        attr = [(apfx+"frame name", 3+len(self.name))]

        if self.class_name is not None:
            text += " [%s]" % self.class_name
            attr.append((apfx+"frame class", len(self.class_name)+3))

        loc = " %s:%d" % (self.filename, self.line)
        text += loc
        attr.append((apfx+"frame location", len(loc)))

        return make_canvas([text], [attr], maxcol, apfx+"frame location")

    def keypress(self, size, key):
        return key


class BreakpointFrame(urwid.FlowWidget):
    def __init__(self, is_current, filename, breakpoint):
        self.is_current = is_current
        self.filename = filename
        self.breakpoint = breakpoint
        self.line = breakpoint.line  # Starts at 1
        self.enabled = breakpoint.enabled
        self.hits = breakpoint.hits

    def selectable(self):
        return True

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        maxcol = size[0]
        if focus:
            apfx = "focused "
        else:
            apfx = ""

        bp_pfx = ''
        if not self.enabled:
            apfx += "disabled "
            bp_pfx += "X"
        if self.is_current:
            apfx += "current "
            bp_pfx += ">>"
        bp_pfx = bp_pfx.ljust(3)

        hits_label = 'hits' if self.hits != 1 else 'hit'
        loc = " %s:%d (%s %s)" % (self.filename, self.line, self.hits, hits_label)
        text = bp_pfx+loc
        attr = [(apfx+"breakpoint", len(loc))]

        return make_canvas([text], [attr], maxcol, apfx+"breakpoint")

    def keypress(self, size, key):
        return key


class SearchController(object):
    def __init__(self, ui):
        self.ui = ui
        self.highlight_line = None

        self.search_box = None
        self.last_search_string = None

    def cancel_highlight(self):
        if self.highlight_line is not None:
            self.highlight_line.set_highlight(False)
            self.highlight_line = None

    def cancel_search(self):
        self.cancel_highlight()
        self.hide_search_ui()

    def hide_search_ui(self):
        self.search_box = None
        del self.ui.lhs_col.contents[0]
        self.ui.lhs_col.set_focus(self.ui.lhs_col.widget_list[0])

    def open_search_ui(self):
        lhs_col = self.ui.lhs_col

        if self.search_box is None:
            _, self.search_start = self.ui.source.get_focus()

            self.search_box = SearchBox(self)
            self.search_AttrMap = urwid.AttrMap(
                    self.search_box, "search box")

            lhs_col.item_types.insert(
                    0, ("flow", None))
            lhs_col.widget_list.insert(0, self.search_AttrMap)

            self.ui.columns.set_focus(lhs_col)
            lhs_col.set_focus(self.search_AttrMap)
        else:
            self.ui.columns.set_focus(lhs_col)
            lhs_col.set_focus(self.search_AttrMap)
            #self.search_box.restart_search()

    def perform_search(self, dir, s=None, start=None, update_search_start=False):
        self.cancel_highlight()

        # self.ui.lhs_col.set_focus(self.ui.lhs_col.widget_list[1])

        if s is None:
            s = self.last_search_string

            if s is None:
                self.ui.message("No previous search term.")
                return False
        else:
            self.last_search_string = s

        if start is None:
            start = self.search_start

        case_insensitive = s.lower() == s

        if start > len(self.ui.source):
            start = 0

        i = (start+dir) % len(self.ui.source)

        if i >= len(self.ui.source):
            i = 0

        while i != start:
            sline = self.ui.source[i].text
            if case_insensitive:
                sline = sline.lower()

            if s in sline:
                sl = self.ui.source[i]
                sl.set_highlight(True)
                self.highlight_line = sl
                self.ui.source.set_focus(i)

                if update_search_start:
                    self.search_start = i

                return True

            i = (i+dir) % len(self.ui.source)

        return False


class SearchBox(urwid.Edit):
    def __init__(self, controller):
        urwid.Edit.__init__(self, [("label", "Search: ")], "")
        self.controller = controller

    def restart_search(self):
        from time import time
        now = time()

        if self.search_start_time > 5:
            self.set_edit_text("")

        self.search_time = now

    def keypress(self, size, key):
        result = urwid.Edit.keypress(self, size, key)
        txt = self.get_edit_text()

        if result is not None:
            if key == "esc":
                self.controller.cancel_search()
                return None
            elif key == "enter":
                if txt:
                    self.controller.hide_search_ui()
                    self.controller.perform_search(dir=1, s=txt,
                            update_search_start=True)
                else:
                    self.controller.cancel_search()
                return None
        else:
            if self.controller.perform_search(dir=1, s=txt):
                self.controller.search_AttrMap.set_attr_map({None: "search box"})
            else:
                self.controller.search_AttrMap.set_attr_map(
                        {None: "search not found"})

        return result

# }}}
