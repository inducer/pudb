import urwid


TABSTOP = 8


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

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        from pudb.debugger import CONFIG
        render_line_nr = CONFIG["line_numbers"]

        maxcol = size[0]
        hscroll = self.dbg_ui.source_hscroll_start

        # attrs is a list of words like 'focused' and 'breakpoint'
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

        text = self.text
        if not attrs and self.attr is not None:
            attr = self.attr + [("source", None)]
        else:
            attr = [(" ".join(attrs+["source"]), None)]

        from urwid.util import apply_target_encoding, trim_text_attr_cs

        # build line prefix ---------------------------------------------------
        line_prefix = ""
        line_prefix_attr = []

        if render_line_nr:
            line_prefix_attr = [("line number", len(self.line_nr))]
            line_prefix = self.line_nr

        line_prefix = crnt+bp+line_prefix
        line_prefix_attr = [("source", 1), ("breakpoint marker", 1)] \
                + line_prefix_attr

        # assume rendered width is same as len
        line_prefix_len = len(line_prefix)

        encoded_line_prefix, line_prefix_cs = apply_target_encoding(line_prefix)

        assert len(encoded_line_prefix) == len(line_prefix)
        # otherwise we'd have to adjust line_prefix_attr... :/

        # shipout, encoding ---------------------------------------------------
        cs = []
        encoded_text_segs = []
        encoded_attr = []

        i = 0
        for seg_attr, seg_len in attr:
            if seg_len is None:
                # means: gobble up remainder of text and rest of line
                # and fill with attribute

                l = hscroll+maxcol
                remaining_text = text[i:]
                encoded_seg_text, seg_cs = apply_target_encoding(
                        remaining_text + l*" ")
                encoded_attr.append((seg_attr, len(remaining_text)+l))
            else:
                unencoded_seg_text = text[i:i+seg_len]
                encoded_seg_text, seg_cs = apply_target_encoding(unencoded_seg_text)

                adjustment = len(encoded_seg_text) - len(unencoded_seg_text)

                encoded_attr.append((seg_attr, seg_len + adjustment))

                i += seg_len

            encoded_text_segs.append(encoded_seg_text)
            cs.extend(seg_cs)

        encoded_text = b"".join(encoded_text_segs)
        encoded_text, encoded_attr, cs = trim_text_attr_cs(
                encoded_text, encoded_attr, cs,
                hscroll, hscroll+maxcol-line_prefix_len)

        encoded_text = encoded_line_prefix + encoded_text
        encoded_attr = line_prefix_attr + encoded_attr
        cs = line_prefix_cs + cs

        return urwid.TextCanvas([encoded_text], [encoded_attr], [cs], maxcol=maxcol)

    def keypress(self, size, key):
        return key


def format_source(debugger_ui, lines, breakpoints):
    lineno_format = "%%%dd " % (len(str(len(lines))))
    try:
        import pygments  # noqa
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
