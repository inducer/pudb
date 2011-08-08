import urwid

TABSTOP=8


class SourceLine(urwid.FlowWidget):
    def __init__(self, dbg_ui, text, line_nr='', attr=None, has_breakpoint=False):
        self.dbg_ui = dbg_ui
        self.text = text
        self.attr = attr
        self.line_nr = line_nr
        self.has_breakpoint = has_breakpoint
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
        from pudb import CONFIG
        render_line_nr = CONFIG["line_numbers"]

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
            if not self.has_breakpoint:
                attrs.append("highlighted")

        if not attrs and self.attr is not None:
            attr = self.attr
            if render_line_nr:
                attr = [("line number", len(self.line_nr))] + attr
        else:
            attr = [(" ".join(attrs+["source"]), hscroll+maxcol-2)]

        from urwid.util import rle_subseg, rle_len

        text = self.text
        if self.dbg_ui.source_hscroll_start:
            text = text[hscroll:]
            attr = rle_subseg(attr,
                    self.dbg_ui.source_hscroll_start,
                    rle_len(attr))

        if render_line_nr:
            text = self.line_nr + text

        text = crnt+bp+text
        attr = [("source", 1), ("bp_star", 1)] + attr

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





def format_source(debugger_ui, lines, breakpoints):
    lineno_format = "%%%dd "%(len(str(len(lines))))
    try:
        import pygments
    except ImportError:
        return [SourceLine(debugger_ui,
            line.rstrip("\n\r").expandtabs(TABSTOP),
            lineno_format % (i+1), None,
            has_breakpoint=i+1 in breakpoints)
            for i, line in enumerate(lines)]
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
                t.Name.Function: "name",
                t.Name.Class: "name",
                t.Punctuation: "punctuation",
                t.String: "string",
                # XXX: Single and Double don't actually work yet.
                # See https://bitbucket.org/birkenfeld/pygments-main/issue/685
                t.String.Double: "doublestring",
                t.String.Single: "singlestring",
                t.String.Backtick: "backtick",
                t.String.Doc: "docstring",
                t.Comment: "comment",
                }

        class UrwidFormatter(Formatter):
            def __init__(subself, **options):
                Formatter.__init__(subself, **options)
                subself.current_line = ""
                subself.current_attr = []
                subself.lineno = 1

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
                            SourceLine(debugger_ui,
                                subself.current_line,
                                lineno_format % subself.lineno,
                                subself.current_attr,
                                has_breakpoint=subself.lineno in breakpoints))
                    subself.current_line = ""
                    subself.current_attr = []
                    subself.lineno += 1

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

        highlight("".join(l.expandtabs(TABSTOP) for l in lines),
                PythonLexer(stripnl=False), UrwidFormatter())

        return result

