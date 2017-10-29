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


THEMES = [
        "classic",
        "vim",
        "dark vim",
        "midnight",
        "solarized",
        "agr-256",
        "monokai",
        "monokai-256"
        ]

from pudb.py3compat import execfile, raw_input
import urwid


def get_palette(may_use_fancy_formats, theme="classic"):
    if may_use_fancy_formats:
        def add_setting(color, setting):
            return color+","+setting
    else:
        def add_setting(color, setting):
            return color

    # ------------------------------------------------------------------------------
    # Reference for some palette items:
    #
    #  "namespace" : "import", "from", "using"
    #  "operator"  : "+", "-", "=" etc.
    #                NOTE: Does not include ".", which is assigned the type "source"
    #  "argument"  : Function arguments
    #  "builtin"   : "range", "dict", "set", "list", etc.
    #  "pseudo"    : "None", "True", "False"
    #                NOTE: Does not include "self", which is assigned the
    #                type "source"
    #  "dunder"    : Class method names of the form __<name>__ within
    #               a class definition
    #  "exception" : Exception names
    #  "keyword"   : All keywords except those specifically assigned to "keyword2"
    #                ("from", "and", "break", "is", "try", "pass", etc.)
    #  "keyword2"  : "class", "def", "exec", "lambda", "print"
    # ------------------------------------------------------------------------------

    inheritance_map = (
        # Style       Inherits from
        # ----------  ----------
        ("namespace", "keyword"),
        ("operator",  "source"),
        ("argument",  "source"),
        ("builtin",   "source"),
        ("pseudo",    "source"),
        ("dunder",    "name"),
        ("exception", "source"),
        ("keyword2",  "keyword")
    )

    palette_dict = {
        # The following styles are initialized to "None".  Themes
        # (including custom Themes) may set them as needed.
        # If they are not set by a theme, then they will
        # inherit from other styles in accordance with
        # the inheritance_map.
        "namespace": None,
        "operator":  None,
        "argument":  None,
        "builtin":   None,
        "pseudo":    None,
        "dunder":    None,
        "exception": None,
        "keyword2":  None,

        # {{{ ui
        "header": ("black", "light gray", "standout"),

        "selectable": ("black", "dark cyan"),
        "focused selectable": ("black", "dark green"),

        "button": (add_setting("white", "bold"), "dark blue"),
        "focused button": ("light cyan", "black"),

        "dialog title": (add_setting("white", "bold"), "dark cyan"),

        "background": ("black", "light gray"),
        "hotkey": (add_setting("black", "underline"), "light gray", "underline"),
        "focused sidebar": (add_setting("yellow", "bold"), "light gray", "standout"),

        "warning": (add_setting("white", "bold"), "dark red", "standout"),

        "label": ("black", "light gray"),
        "value": (add_setting("yellow", "bold"), "dark blue"),
        "fixed value": ("light gray", "dark blue"),
        "group head": (add_setting("dark blue", "bold"), "light gray"),

        "search box": ("black", "dark cyan"),
        "search not found": ("white", "dark red"),

        # }}}

        # {{{ shell

        "command line edit": (add_setting("yellow", "bold"), "dark blue"),
        "command line prompt": (add_setting("white", "bold"), "dark blue"),

        "command line output": ("light cyan", "dark blue"),
        "command line input": (add_setting("light cyan", "bold"), "dark blue"),
        "command line error": (add_setting("light red", "bold"), "dark blue"),

        "focused command line output": ("black", "dark green"),
        "focused command line input": (
                add_setting("light cyan", "bold"),
                "dark green"),
        "focused command line error": ("black", "dark green"),

        "command line clear button": (add_setting("white", "bold"), "dark blue"),
        "command line focused button": ("light cyan", "black"),

        # }}}

        # {{{ source

        "breakpoint": ("black", "dark cyan"),
        "disabled breakpoint": ("dark gray", "dark cyan"),
        "focused breakpoint": ("black", "dark green"),
        "focused disabled breakpoint": ("dark gray", "dark green"),
        "current breakpoint": (add_setting("white", "bold"), "dark cyan"),
        "disabled current breakpoint": (
                add_setting("dark gray", "bold"), "dark cyan"),
        "focused current breakpoint": (
                add_setting("white", "bold"), "dark green", "bold"),
        "focused disabled current breakpoint": (
                add_setting("dark gray", "bold"), "dark green", "bold"),

        "source": (add_setting("yellow", "bold"), "dark blue"),
        "focused source": ("black", "dark green"),
        "highlighted source": ("black", "dark magenta"),
        "current source": ("black", "dark cyan"),
        "current focused source": (add_setting("white", "bold"), "dark cyan"),
        "current highlighted source": ("white", "dark cyan"),

        # {{{ highlighting

        "line number": ("light gray", "dark blue"),
        "keyword": (add_setting("white", "bold"), "dark blue"),
        "name": ("light cyan", "dark blue"),
        "literal": ("light magenta, bold", "dark blue"),

        "string": (add_setting("light magenta", "bold"), "dark blue"),
        "doublestring": (add_setting("light magenta", "bold"), "dark blue"),
        "singlestring": (add_setting("light magenta", "bold"), "dark blue"),
        "docstring": (add_setting("light magenta", "bold"), "dark blue"),

        "punctuation": ("light gray", "dark blue"),
        "comment": ("light gray", "dark blue"),

        # }}}

        # }}}

        # {{{ breakpoints

        "breakpoint marker": ("dark red", "dark blue"),

        "breakpoint source": (add_setting("yellow", "bold"), "dark red"),
        "breakpoint focused source": ("black", "dark red"),
        "current breakpoint source": ("black", "dark red"),
        "current breakpoint focused source": ("white", "dark red"),

        # }}}

        # {{{ variables view

        "variables": ("black", "dark cyan"),
        "variable separator": ("dark cyan", "light gray"),

        "var label": ("dark blue", "dark cyan"),
        "var value": ("black", "dark cyan"),
        "focused var label": ("dark blue", "dark green"),
        "focused var value": ("black", "dark green"),

        "highlighted var label": ("white", "dark cyan"),
        "highlighted var value": ("black", "dark cyan"),
        "focused highlighted var label": ("white", "dark green"),
        "focused highlighted var value": ("black", "dark green"),

        "return label": ("white", "dark blue"),
        "return value": ("black", "dark cyan"),
        "focused return label": ("light gray", "dark blue"),
        "focused return value": ("black", "dark green"),

        # }}}

        # {{{ stack

        "stack": ("black", "dark cyan"),

        "frame name": ("black", "dark cyan"),
        "focused frame name": ("black", "dark green"),
        "frame class": ("dark blue", "dark cyan"),
        "focused frame class": ("dark blue", "dark green"),
        "frame location": ("light cyan", "dark cyan"),
        "focused frame location": ("light cyan", "dark green"),

        "current frame name": (add_setting("white", "bold"),
            "dark cyan"),
        "focused current frame name": (add_setting("white", "bold"),
            "dark green", "bold"),
        "current frame class": ("dark blue", "dark cyan"),
        "focused current frame class": ("dark blue", "dark green"),
        "current frame location": ("light cyan", "dark cyan"),
        "focused current frame location": ("light cyan", "dark green"),

        # }}}

    }

    if theme == "classic":
        pass
    elif theme == "vim":
        # {{{ vim theme

        palette_dict.update({
            "source": ("black", "default"),
            "keyword": ("brown", "default"),
            "kw_namespace": ("dark magenta", "default"),

            "literal": ("black", "default"),
            "string": ("dark red", "default"),
            "doublestring": ("dark red", "default"),
            "singlestring": ("dark red", "default"),
            "docstring": ("dark red", "default"),

            "punctuation": ("black", "default"),
            "comment": ("dark blue", "default"),
            "classname": ("dark cyan", "default"),
            "name": ("dark cyan", "default"),
            "line number": ("dark gray", "default"),
            "breakpoint marker": ("dark red", "default"),

            # {{{ shell

            "command line edit":
            ("black", "default"),
            "command line prompt":
            (add_setting("black", "bold"), "default"),

            "command line output":
            (add_setting("black", "bold"), "default"),
            "command line input":
            ("black", "default"),
            "command line error":
            (add_setting("light red", "bold"), "default"),

            "focused command line output":
            ("black", "dark green"),
            "focused command line input":
            (add_setting("light cyan", "bold"), "dark green"),
            "focused command line error":
            ("black", "dark green"),

            # }}}
            })
        # }}}
    elif theme == "dark vim":
        # {{{ dark vim

        palette_dict.update({
            "header": ("black", "light gray", "standout"),

            # {{{ variables view
            "variables": ("black", "dark gray"),
            "variable separator": ("dark cyan", "light gray"),

            "var label": ("light gray", "dark gray"),
            "var value": ("white", "dark gray"),
            "focused var label": ("light gray", "light blue"),
            "focused var value": ("white", "light blue"),

            "highlighted var label": ("light gray", "dark green"),
            "highlighted var value": ("white", "dark green"),
            "focused highlighted var label": ("light gray", "light blue"),
            "focused highlighted var value": ("white", "light blue"),

            "return label": ("light gray", "dark gray"),
            "return value": ("light cyan", "dark gray"),
            "focused return label": ("yellow", "light blue"),
            "focused return value": ("white", "light blue"),

            # }}}

            # {{{ stack view

            "stack": ("black", "dark gray"),

            "frame name": ("light gray", "dark gray"),
            "focused frame name": ("light gray", "light blue"),
            "frame class": ("dark blue", "dark gray"),
            "focused frame class": ("dark blue", "light blue"),
            "frame location": ("white", "dark gray"),
            "focused frame location": ("white", "light blue"),

            "current frame name": (add_setting("white", "bold"),
                "dark gray"),
            "focused current frame name": (add_setting("white", "bold"),
                "light blue", "bold"),
            "current frame class": ("dark blue", "dark gray"),
            "focused current frame class": ("dark blue", "dark green"),
            "current frame location": ("light cyan", "dark gray"),
            "focused current frame location": ("light cyan", "light blue"),

            # }}}

            # {{{ breakpoint view

            "breakpoint": ("light gray", "dark gray"),
            "disabled breakpoint": ("black", "dark gray"),
            "focused breakpoint": ("light gray", "light blue"),
            "focused disabled breakpoint": ("black", "light blue"),
            "current breakpoint": (add_setting("white", "bold"), "dark gray"),
            "disabled current breakpoint": ("black", "dark gray"),
            "focused current breakpoint":
                (add_setting("white", "bold"), "light blue"),
            "focused disabled current breakpoint":
                ("black", "light blue"),

            # }}}

            # {{{ ui widgets

            "selectable": ("light gray", "dark gray"),
            "focused selectable": ("white", "light blue"),

            "button": ("light gray", "dark gray"),
            "focused button": ("white", "light blue"),

            "background": ("black", "light gray"),
            "hotkey": (add_setting("black", "underline"), "light gray", "underline"),
            "focused sidebar": ("light blue", "light gray", "standout"),

            "warning": (add_setting("white", "bold"), "dark red", "standout"),

            "label": ("black", "light gray"),
            "value": ("white", "dark gray"),
            "fixed value": ("light gray", "dark gray"),

            "search box": ("white", "dark gray"),
            "search not found": ("white", "dark red"),

            "dialog title": (add_setting("white", "bold"), "dark gray"),

            # }}}

            # {{{ source view

            "breakpoint marker": ("dark red", "black"),

            "breakpoint source": ("light gray", "dark red"),
            "breakpoint focused source": ("black", "dark red"),
            "current breakpoint source": ("black", "dark red"),
            "current breakpoint focused source": ("white", "dark red"),

            # }}}

            # {{{ highlighting

            "source": ("white", "black"),
            "focused source": ("white", "light blue"),
            "highlighted source": ("black", "dark magenta"),
            "current source": ("black", "light gray"),
            "current focused source": ("white", "dark cyan"),
            "current highlighted source": ("white", "dark cyan"),

            "line number": ("dark gray", "black"),
            "keyword": ("yellow", "black"),

            "literal": ("dark magenta", "black"),
            "string": ("dark magenta", "black"),
            "doublestring": ("dark magenta", "black"),
            "singlestring": ("dark magenta", "black"),
            "docstring": ("dark magenta", "black"),

            "name": ("light cyan", "black"),
            "punctuation": ("yellow", "black"),
            "comment": ("light blue", "black"),

            # }}}

            # {{{ shell

            "command line edit":
            ("white", "black"),
            "command line prompt":
            (add_setting("yellow", "bold"), "black"),

            "command line output":
            (add_setting("yellow", "bold"), "black"),
            "command line input":
            ("white", "black"),
            "command line error":
            (add_setting("light red", "bold"), "black"),

            "focused command line output":
            ("black", "light blue"),
            "focused command line input":
            (add_setting("light cyan", "bold"), "light blue"),
            "focused command line error":
            ("black", "light blue"),

            # }}}
            })

        # }}}
    elif theme == "midnight":
        # {{{ midnight

        # Based on XCode's midnight theme
        # Looks best in a console with green text against black background
        palette_dict.update({
            "variables": ("white", "default"),

            "var label": ("light blue", "default"),
            "var value": ("white", "default"),

            "stack": ("white", "default"),

            "frame name": ("white", "default"),
            "frame class": ("dark blue", "default"),
            "frame location": ("light cyan", "default"),

            "current frame name": (add_setting("white", "bold"), "default"),
            "current frame class": ("dark blue", "default"),
            "current frame location": ("light cyan", "default"),

            "focused frame name": ("black", "dark green"),
            "focused frame class": (add_setting("white", "bold"), "dark green"),
            "focused frame location": ("dark blue", "dark green"),

            "focused current frame name": ("black", "dark green"),
            "focused current frame class": (
                add_setting("white", "bold"), "dark green"),
            "focused current frame location": ("dark blue", "dark green"),

            "search box": ("default", "default"),

            "breakpoint": ("white", "default"),
            "disabled breakpoint": ("dark gray", "default"),
            "focused breakpoint": ("black", "dark green"),
            "focused disabled breakpoint": ("dark gray", "dark green"),
            "current breakpoint": (add_setting("white", "bold"), "default"),
            "disabled current breakpoint": (
                add_setting("dark gray", "bold"), "default"),
            "focused current breakpoint": (
                add_setting("white", "bold"), "dark green", "bold"),
            "focused disabled current breakpoint": (
                add_setting("dark gray", "bold"), "dark green", "bold"),

            "source": ("white", "default"),
            "highlighted source": ("white", "light cyan"),
            "current source": ("white", "light gray"),
            "current focused source": ("white", "brown"),

            "line number": ("light gray", "default"),
            "keyword": ("dark magenta", "default"),
            "name": ("white", "default"),
            "literal": ("dark cyan", "default"),
            "string": ("dark red", "default"),
            "doublestring": ("dark red", "default"),
            "singlestring": ("light blue", "default"),
            "docstring": ("light red", "default"),
            "backtick": ("light green", "default"),
            "punctuation": ("white", "default"),
            "comment": ("dark green", "default"),
            "classname": ("dark cyan", "default"),
            "funcname": ("white", "default"),

            "breakpoint marker": ("dark red", "default"),

            # {{{ shell

            "command line edit": ("white", "default"),
            "command line prompt": (add_setting("white", "bold"), "default"),

            "command line output": (add_setting("white", "bold"), "default"),
            "command line input": (add_setting("white", "bold"), "default"),
            "command line error": (add_setting("light red", "bold"), "default"),

            "focused command line output": ("black", "dark green"),
            "focused command line input": (
                    add_setting("white", "bold"), "dark green"),
            "focused command line error": ("black", "dark green"),

            "command line clear button": (add_setting("white", "bold"), "default"),
            "command line focused button": ("black", "light gray"),  # White
            # doesn't work in curses mode

            # }}}

        })

        # }}}
    elif theme == "solarized":
        # {{{ solarized
        palette_dict.update({
            # UI
            "header": ("black", "light blue", "standout"),
            "focused sidebar": ("yellow", "light blue", "standout"),
            "group head": ("black", "light blue"),
            "background": ("black", "light blue"),
            "label": ("black", "light blue"),
            "value": ("white", "dark blue"),
            "fixed value": ("black", "light blue"),

            "variables": ("light blue", "default"),

            "var label": ("dark blue", "default"),
            "var value": ("light blue", "default"),

            "focused var label": ("white", "dark blue"),
            "focused var value": ("black", "dark blue"),

            "highlighted var label": ("white", "light green"),
            "highlighted var value": ("white", "light green"),
            "focused highlighted var label": ("white", "light green"),
            "focused highlighted var value": ("white", "light green"),

            "stack": ("light blue", "default"),

            "frame name": ("dark blue", "default"),
            "frame class": ("light blue", "default"),
            "frame location": ("light green", "default"),

            "focused frame name": ("white", "dark blue"),
            "focused frame class": ("black", "dark blue"),
            "focused frame location": ("dark gray", "dark blue"),

            "focused current frame name": ("white", "light green"),
            "focused current frame class": ("black", "light green"),
            "focused current frame location": ("dark gray", "light green"),

            "current frame name": ("white", "light green"),
            "current frame class": ("black", "light green"),
            "current frame location": ("dark gray", "light green"),

            # breakpoints
            "breakpoint": ("light blue", "default"),
            "disabled breakpoint": ("light gray", "default"),
            "focused breakpoint": ("white", "light green"),
            "focused disabled breakpoint": ("light gray", "light green"),
            "current breakpoint": ("white", "dark blue"),
            "disabled current breakpoint": ("light gray", "dark blue"),
            "focused current breakpoint": ("white", "light green"),
            "focused disabled current breakpoint": ("light gray", "light green"),

            # source
            "breakpoint source": ("light blue", "black"),
            "current breakpoint source": ("black", "light green"),
            "breakpoint focused source": ("dark gray", "dark blue"),
            "current breakpoint focused source": ("black", "light green"),
            "breakpoint marker": ("dark red", "default"),

            "search box": ("default", "default"),

            "source": ("light blue", "default"),
            "current source": ("light gray", "light blue"),
            "current focused source": ("light gray", "light blue"),

            "focused source": ("dark gray", "dark blue"),

            "current highlighted source": ("black", "dark cyan"),
            "highlighted source": ("light blue", "black"),

            "line number": ("light blue", "default"),
            "keyword": ("dark green", "default"),
            "name": ("light blue", "default"),
            "literal": ("dark cyan", "default"),
            "string": ("dark cyan", "default"),
            "doublestring": ("dark cyan", "default"),
            "singlestring": ("light blue", "default"),
            "docstring": ("dark cyan", "default"),
            "backtick": ("light green", "default"),
            "punctuation": ("light blue", "default"),
            "comment": ("light green", "default"),
            "classname": ("dark blue", "default"),
            "funcname": ("dark blue", "default"),

            # shell

            "command line edit": ("light blue", "default"),
            "command line prompt": ("light blue", "default"),

            "command line output": ("light blue", "default"),
            "command line input": ("light blue", "default"),
            "command line error": ("dark red", "default"),

            "focused command line output": ("black", "light green"),
            "focused command line input": ("black", "light green"),
            "focused command line error": ("dark red", "light blue"),

            "command line clear button": ("light blue", "default"),
            "command line focused button": ("black", "light blue"),
        })

    # }}}
    elif theme == "agr-256":
        # {{{ agr-256
        palette_dict.update({
            "header": ("h235", "h252", "standout"),

            # {{{ variables view
            "variables": ("h235", "h233"),
            "variable separator": ("h23", "h252"),

            "var label": ("h111", "h233"),
            "var value": ("h255", "h233"),
            "focused var label": ("h192", "h24"),
            "focused var value": ("h192", "h24"),

            "highlighted var label": ("h252", "h22"),
            "highlighted var value": ("h255", "h22"),
            "focused highlighted var label": ("h252", "h64"),
            "focused highlighted var value": ("h255", "h64"),

            "return label": ("h113", "h233"),
            "return value": ("h113", "h233"),
            "focused return label": (add_setting("h192", "bold"), "h24"),
            "focused return value": ("h192", "h24"),
            # }}}

            # {{{ stack view
            "stack": ("h235", "h233"),

            "frame name": ("h192", "h233"),
            "focused frame name": ("h192", "h24"),
            "frame class": ("h111", "h233"),
            "focused frame class": ("h192", "h24"),
            "frame location": ("h252", "h233"),
            "focused frame location": ("h192", "h24"),

            "current frame name": ("h255", "h22"),
            "focused current frame name": ("h255", "h64"),
            "current frame class": ("h111", "h22"),
            "focused current frame class": ("h255", "h64"),
            "current frame location": ("h252", "h22"),
            "focused current frame location": ("h255", "h64"),
            # }}}

            # {{{ breakpoint view
            "breakpoint": ("h80", "h233"),
            "disabled breakpoint": ("h60", "h233"),
            "focused breakpoint": ("h192", "h24"),
            "focused disabled breakpoint": ("h182", "h24"),
            "current breakpoint": (add_setting("h255", "bold"), "h22"),
            "disabled current breakpoint": (add_setting("h016", "bold"), "h22"),
            "focused current breakpoint": (add_setting("h255", "bold"), "h64"),
            "focused disabled current breakpoint": (
                add_setting("h016", "bold"), "h64"),
            # }}}

            # {{{ ui widgets

            "selectable": ("h252", "h235"),
            "focused selectable": ("h255", "h24"),

            "button": ("h252", "h235"),
            "focused button": ("h255", "h24"),

            "background": ("h235", "h252"),
            "hotkey": (add_setting("h235", "underline"), "h252", "underline"),
            "focused sidebar": ("h23", "h252", "standout"),

            "warning": (add_setting("h255", "bold"), "h124", "standout"),

            "label": ("h235", "h252"),
            "value": ("h255", "h17"),
            "fixed value": ("h252", "h17"),
            "group head": (add_setting("h25", "bold"), "h252"),

            "search box": ("h255", "h235"),
            "search not found": ("h255", "h124"),

            "dialog title": (add_setting("h255", "bold"), "h235"),

            # }}}

            # {{{ source view
            "breakpoint marker": ("h160", "h235"),

            "breakpoint source": ("h252", "h124"),
            "breakpoint focused source": ("h192", "h124"),
            "current breakpoint source": ("h192", "h124"),
            "current breakpoint focused source": (
                    add_setting("h192", "bold"), "h124"),
            # }}}

            # {{{ highlighting
            "source": ("h255", "h235"),
            "focused source": ("h192", "h24"),
            "highlighted source": ("h252", "h22"),
            "current source": (add_setting("h252", "bold"), "h23"),
            "current focused source": (add_setting("h192", "bold"), "h23"),
            "current highlighted source": ("h255", "h22"),

            "line number": ("h241", "h235"),
            "keyword": ("h111", "h235"),

            "literal": ("h173", "h235"),
            "string": ("h113", "h235"),
            "doublestring": ("h113", "h235"),
            "singlestring": ("h113", "h235"),
            "docstring": ("h113", "h235"),

            "name": ("h192", "h235"),
            "punctuation": ("h223", "h235"),
            "comment": ("h246", "h235"),

            # }}}

            # {{{ shell
            "command line edit": ("h255", "h233"),
            "command line prompt": (add_setting("h192", "bold"), "h233"),

            "command line output": ("h80", "h233"),
            "command line input": ("h255", "h233"),
            "command line error": ("h160", "h233"),

            "focused command line output": (add_setting("h192", "bold"), "h24"),
            "focused command line input": ("h255", "h24"),
            "focused command line error": ("h235", "h24"),

            "command line clear button": (add_setting("h255", "bold"), "h233"),
            "command line focused button": ("h255", "h24"),
            # }}}
        })
        # }}}
    elif theme == "monokai":
        # {{{ midnight

        # Based on XCode's midnight theme
        # Looks best in a console with green text against black background
        palette_dict.update({
            "variables": ("white", "default"),

            "var label": ("light blue", "default"),
            "var value": ("white", "default"),

            "stack": ("white", "default"),

            "frame name": ("white", "default"),
            "frame class": ("dark blue", "default"),
            "frame location": ("light cyan", "default"),

            "current frame name": (add_setting("white", "bold"), "default"),
            "current frame class": ("dark blue", "default"),
            "current frame location": ("light cyan", "default"),

            "focused frame name": ("black", "dark green"),
            "focused frame class": (add_setting("white", "bold"), "dark green"),
            "focused frame location": ("dark blue", "dark green"),

            "focused current frame name": ("black", "dark green"),
            "focused current frame class": (
                add_setting("white", "bold"), "dark green"),
            "focused current frame location": ("dark blue", "dark green"),

            "search box": ("default", "default"),

            "breakpoint": ("white", "default"),
            "disabled breakpoint": ("dark gray", "default"),
            "focused breakpoint": ("black", "dark green"),
            "focused disabled breakpoint": ("dark gray", "dark green"),
            "current breakpoint": (add_setting("white", "bold"), "default"),
            "disabled current breakpoint": (
                add_setting("dark gray", "bold"), "default"),
            "focused current breakpoint": (
                add_setting("white", "bold"), "dark green", "bold"),
            "focused disabled current breakpoint": (
                add_setting("dark gray", "bold"), "dark green", "bold"),

            "source": ("white", "default"),
            "highlighted source": ("white", "light cyan"),
            "current source": ("white", "light gray"),
            "current focused source": ("white", "brown"),

            "line number": ("dark gray", "black"),
            "keyword2": ("light cyan", "black"),
            "name": ("light green", "black"),
            "literal": ("light magenta", "black"),

            "namespace": ("light red", "black"),
            "operator": ("light red", "black"),
            "argument": ("brown", "black"),
            "builtin": ("light cyan", "black"),
            "pseudo": ("light magenta", "black"),
            "dunder": ("light cyan", "black"),
            "exception": ("light cyan", "black"),
            "keyword": ("light red", "black"),

            "string": ("dark red", "default"),
            "doublestring": ("dark red", "default"),
            "singlestring": ("light blue", "default"),
            "docstring": ("light red", "default"),
            "backtick": ("light green", "default"),
            "punctuation": ("white", "default"),
            "comment": ("dark green", "default"),
            "classname": ("dark cyan", "default"),
            "funcname": ("white", "default"),

            "breakpoint marker": ("dark red", "default"),

            # {{{ shell

            "command line edit": ("white", "default"),
            "command line prompt": (add_setting("white", "bold"), "default"),

            "command line output": (add_setting("white", "bold"), "default"),
            "command line input": (add_setting("white", "bold"), "default"),
            "command line error": (add_setting("light red", "bold"), "default"),

            "focused command line output": ("black", "dark green"),
            "focused command line input": (
                    add_setting("white", "bold"), "dark green"),
            "focused command line error": ("black", "dark green"),

            "command line clear button": (add_setting("white", "bold"), "default"),
            "command line focused button": ("black", "light gray"),  # White
            # doesn't work in curses mode

            # }}}

        })

        # }}}
    elif theme == "monokai-256":
        # {{{ monokai-256
        palette_dict.update({
            "header": ("h235", "h252", "standout"),

            # {{{ variables view
            "variables": ("h235", "h233"),
            "variable separator": ("h23", "h252"),

            "var label": ("h111", "h233"),
            "var value": ("h255", "h233"),
            "focused var label": ("h237", "h172"),
            "focused var value": ("h237", "h172"),

            "highlighted var label": ("h252", "h22"),
            "highlighted var value": ("h255", "h22"),
            "focused highlighted var label": ("h252", "h64"),
            "focused highlighted var value": ("h255", "h64"),

            "return label": ("h113", "h233"),
            "return value": ("h113", "h233"),
            "focused return label": (add_setting("h192", "bold"), "h24"),
            "focused return value": ("h237", "h172"),
            # }}}

            # {{{ stack view
            "stack": ("h235", "h233"),

            "frame name": ("h192", "h233"),
            "focused frame name": ("h237", "h172"),
            "frame class": ("h111", "h233"),
            "focused frame class": ("h237", "h172"),
            "frame location": ("h252", "h233"),
            "focused frame location": ("h237", "h172"),

            "current frame name": ("h255", "h22"),
            "focused current frame name": ("h255", "h64"),
            "current frame class": ("h111", "h22"),
            "focused current frame class": ("h255", "h64"),
            "current frame location": ("h252", "h22"),
            "focused current frame location": ("h255", "h64"),
            # }}}

            # {{{ breakpoint view
            "breakpoint": ("h80", "h233"),
            "disabled breakpoint": ("h60", "h233"),
            "focused breakpoint": ("h237", "h172"),
            "focused disabled breakpoint": ("h182", "h24"),
            "current breakpoint": (add_setting("h255", "bold"), "h22"),
            "disabled current breakpoint": (add_setting("h016", "bold"), "h22"),
            "focused current breakpoint": (add_setting("h255", "bold"), "h64"),
            "focused disabled current breakpoint": (
                add_setting("h016", "bold"), "h64"),
            # }}}

            # {{{ ui widgets

            "selectable": ("h252", "h235"),
            "focused selectable": ("h255", "h24"),

            "button": ("h252", "h235"),
            "focused button": ("h255", "h24"),

            "background": ("h235", "h252"),
            "hotkey": (add_setting("h235", "underline"), "h252", "underline"),
            "focused sidebar": ("h23", "h252", "standout"),

            "warning": (add_setting("h255", "bold"), "h124", "standout"),

            "label": ("h235", "h252"),
            "value": ("h255", "h17"),
            "fixed value": ("h252", "h17"),
            "group head": (add_setting("h25", "bold"), "h252"),

            "search box": ("h255", "h235"),
            "search not found": ("h255", "h124"),

            "dialog title": (add_setting("h255", "bold"), "h235"),

            # }}}

            # {{{ source view
            "breakpoint marker": ("h160", "h235"),

            "breakpoint source": ("h252", "h124"),
            "breakpoint focused source": ("h192", "h124"),
            "current breakpoint source": ("h192", "h124"),
            "current breakpoint focused source": (
                    add_setting("h192", "bold"), "h124"),
            # }}}

            # {{{ highlighting
            "source": ("h255", "h235"),
            "focused source": ("h237", "h172"),
            "highlighted source": ("h252", "h22"),
            "current source": (add_setting("h252", "bold"), "h23"),
            "current focused source": (add_setting("h192", "bold"), "h23"),
            "current highlighted source": ("h255", "h22"),

            "line number": ("h241", "h235"),
            "keyword2": ("h51", "h235"),
            "name": ("h155", "h235"),
            "literal": ("h141", "h235"),

            "namespace": ("h198", "h235"),
            "operator": ("h198", "h235"),
            "argument": ("h208", "h235"),
            "builtin": ("h51", "h235"),
            "pseudo": ("h141", "h235"),
            "dunder": ("h51", "h235"),
            "exception": ("h51", "h235"),
            "keyword": ("h198", "h235"),

            "string": ("h228", "h235"),
            "doublestring": ("h228", "h235"),
            "singlestring": ("h228", "h235"),
            "docstring": ("h243", "h235"),

            "punctuation": ("h255", "h235"),
            "comment": ("h243", "h235"),

            # }}}

            # {{{ shell
            "command line edit": ("h255", "h233"),
            "command line prompt": (add_setting("h192", "bold"), "h233"),

            "command line output": ("h80", "h233"),
            "command line input": ("h255", "h233"),
            "command line error": ("h160", "h233"),

            "focused command line output": (add_setting("h192", "bold"), "h24"),
            "focused command line input": ("h255", "h24"),
            "focused command line error": ("h235", "h24"),

            "command line clear button": (add_setting("h255", "bold"), "h233"),
            "command line focused button": ("h255", "h24"),
            # }}}
        })
        # }}}

    else:
        try:
            symbols = {
                    "palette": palette_dict,
                    "add_setting": add_setting,
                    }

            from os.path import expanduser, expandvars
            execfile(expanduser(expandvars(theme)), symbols)
        except Exception:
            print("Error when importing theme:")
            from traceback import print_exc
            print_exc()
            raw_input("Hit enter:")

    # Apply style inheritance
    for child, parent in inheritance_map:
        if palette_dict[child] is None:
            palette_dict[child] = palette_dict[parent]

    palette_list = []
    for setting_name, color_values in palette_dict.items():
        fg_color = color_values[0].lower().strip()
        bg_color = color_values[1].lower().strip()

        # Convert hNNN syntax to equivalent #RGB value
        # (https://github.com/wardi/urwid/issues/24)
        if fg_color.startswith('h') or bg_color.startswith('h'):
            attr = urwid.AttrSpec(fg_color, bg_color, colors=256)
            palette_list.append((setting_name, 'default', 'default', 'default',
                attr.foreground,
                attr.background))
        else:
            palette_list.append((setting_name,) + color_values)

    return palette_list

# vim: foldmethod=marker
