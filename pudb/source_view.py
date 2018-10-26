from __future__ import absolute_import, division, print_function

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

        if render_line_nr and self.line_nr:
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

                rowlen = hscroll+maxcol
                remaining_text = text[i:]
                encoded_seg_text, seg_cs = apply_target_encoding(
                        remaining_text + rowlen*" ")
                encoded_attr.append((seg_attr, len(remaining_text)+rowlen))
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
        argument_parser = ArgumentParser(t)

        # NOTE: Tokens of the form t.Token.<name> are not native
        #       Pygments token types; they are user defined token
        #       types.
        #
        #       t.Token is a Pygments token creator object
        #       (see http://pygments.org/docs/tokens/)
        #
        #       The user defined token types get assigned by
        #       one of several translation operations at the
        #       beginning of add_snippet().
        #
        ATTR_MAP = {  # noqa: N806
                t.Token: "source",
                t.Keyword.Namespace: "namespace",
                t.Token.Argument: "argument",
                t.Token.Dunder: "dunder",
                t.Token.Keyword2: 'keyword2',
                t.Keyword: "keyword",
                t.Literal: "literal",
                t.Name.Exception: "exception",
                t.Name.Function: "name",
                t.Name.Class: "name",
                t.Name.Builtin: "builtin",
                t.Name.Builtin.Pseudo: "pseudo",
                t.Punctuation: "punctuation",
                t.Operator: "operator",
                t.String: "string",
                # XXX: Single and Double don't actually work yet.
                # See https://bitbucket.org/birkenfeld/pygments-main/issue/685
                t.String.Double: "doublestring",
                t.String.Single: "singlestring",
                t.String.Backtick: "backtick",
                t.String.Doc: "docstring",
                t.Comment: "comment",
                }

        # Token translation table. Maps token types and their
        # associated strings to new token types.
        ATTR_TRANSLATE = {  # noqa: N806
                t.Keyword: {
                    'class': t.Token.Keyword2,
                    'def': t.Token.Keyword2,
                    'exec': t.Token.Keyword2,
                    'lambda': t.Token.Keyword2,
                    'print': t.Token.Keyword2,
                    },
                t.Operator: {
                    '.': t.Token,
                    },
                t.Name.Builtin.Pseudo: {
                    'self': t.Token,
                    },
                t.Name.Builtin: {
                    'object': t.Name.Class,
                    },
                }

        class UrwidFormatter(Formatter):
            def __init__(subself, **options):  # noqa: N805
                Formatter.__init__(subself, **options)
                subself.current_line = ""
                subself.current_attr = []
                subself.lineno = 1

            def format(subself, tokensource, outfile):  # noqa: N805
                def add_snippet(ttype, s):
                    if not s:
                        return

                    # Find function arguments. When found, change their
                    # ttype to t.Token.Argument
                    new_ttype = argument_parser.parse_token(ttype, s)
                    if new_ttype:
                        ttype = new_ttype

                    # Translate tokens
                    if ttype in ATTR_TRANSLATE:
                        if s in ATTR_TRANSLATE[ttype]:
                            ttype = ATTR_TRANSLATE[ttype][s]

                    # Translate dunder method tokens
                    if ttype == (
                            t.Name.Function
                            and s.startswith('__') and s.endswith('__')
                            ):
                        ttype = t.Token.Dunder

                    while ttype not in ATTR_MAP:
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


class ParseState(object):
    '''States for the ArgumentParser class'''
    idle = 1
    found_function = 2
    found_open_paren = 3


class ArgumentParser(object):
    '''Parse source code tokens and identify function arguments.

    This parser implements a state machine which accepts
    Pygments tokens, delivered sequentially from the beginning
    of a source file to its end.

    parse_token() processes each token (and its associated string)
    and returns None if that token does not require modification.
    When it finds a token which represents a function
    argument, it returns the correct token type for that
    item (the caller should then replace the associated item's
    token type with the returned type)
    '''

    def __init__(self, pygments_token):
        self.t = pygments_token
        self.state = ParseState.idle
        self.paren_level = 0

    def parse_token(self, token, s):
        '''Parse token. Return None or replacement token type'''
        if self.state == ParseState.idle:
            if token is self.t.Name.Function:
                self.state = ParseState.found_function
                self.paren_level = 0
        elif self.state == ParseState.found_function:
            if token is self.t.Punctuation and s == '(':
                self.state = ParseState.found_open_paren
                self.paren_level = 1
        else:
            if ((token is self.t.Name)
                    or (token is self.t.Name.Builtin.Pseudo and s == 'self')):
                return self.t.Token.Argument
            elif token is self.t.Punctuation and s == ')':
                self.paren_level -= 1
            elif token is self.t.Punctuation and s == '(':
                self.paren_level += 1
            if self.paren_level == 0:
                self.state = ParseState.idle
        return None
