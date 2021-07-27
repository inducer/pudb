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

from dataclasses import dataclass, astuple, replace
from typing import Optional
from pudb.lowlevel import ui_log

THEMES = [
    "classic",
    "vim",
    "dark vim",
    "midnight",
    "solarized",
    "agr-256",
    "monokai",
    "monokai-256",
    "mono",
]


@dataclass
class PaletteEntry:
    name: str
    foreground: str = "default"
    background: str = "default"
    mono: Optional[str] = None
    foreground_high: Optional[str] = None
    background_high: Optional[str] = None

    def handle_256_colors(self):
        if self.foreground.lower().strip().startswith("h"):
            self.foreground_high = self.foreground
            self.foreground = "default"
        if self.background.lower().strip().startswith("h"):
            self.background_high = self.background
            self.background = "default"


# ------------------------------------------------------------------------------
# Reference for some palette items:
#
#  "namespace" : "import", "from", "using"
#  "operator"  : "+", "-", "=" etc.
#                NOTE: Does not include ".", which is assigned the type "source"
#  "argument"  : Function arguments
#  "builtin"   : "range", "dict", "set", "list", etc.
#  "pseudo"    : "self", "cls"
#  "dunder"    : Class method names of the form __<name>__ within
#               a class definition
#  "magic"     : Subset of "dunder", methods that the python language assigns
#               special meaning to. ("__str__", "__init__", etc.)
#  "exception" : Exception names
#  "keyword"   : All keywords except those specifically assigned to "keyword2"
#                ("from", "and", "break", "is", "try", "True", "None", etc.)
#  "keyword2"  : "class", "def", "exec", "lambda", "print"
# ------------------------------------------------------------------------------


# {{{ style inheritance
BASE_STYLES = {
    "background":         None,
    "selectable":         None,
    "focused selectable": None,
    "highlighted":        None,
    "hotkey":             None,
}


# Map styles to their parent. If a style is not defined, use the parent style
# recursively.
# focused > highlighted > current > breakpoint line/disabled breakpoint
CLEAN_INHERITANCE_MAP = {
    # {{{ general ui
    "label": "background",
    "header": "background",
    "dialog title": "header",
    "group head": "header",
    "focused sidebar": "header",

    "input": "selectable",
    "focused input": "focused selectable",
    "button": "input",
    "focused button": "focused input",
    "value": "input",
    "fixed value": "label",

    "warning": "highlighted",
    "search box": "focused input",
    "search not found": "warning",
    # }}}

    # {{{ source view
    "source": "selectable",
    "focused source": "focused selectable",
    "highlighted source": "highlighted",

    "current source": "source",
    "current focused source": "focused source",
    "current highlighted source": "current source",

    "breakpoint source": "source",
    "breakpoint focused source": "focused source",
    "current breakpoint source": "current source",
    "current breakpoint focused source": "current focused source",

    "line number": "source",
    "breakpoint marker": "line number",
    "current line marker": "breakpoint marker",
    # }}}

    # {{{ sidebar
    "sidebar one": "selectable",
    "sidebar two": "selectable",
    "sidebar three": "selectable",

    "focused sidebar one": "focused selectable",
    "focused sidebar two": "focused selectable",
    "focused sidebar three": "focused selectable",
    # }}}

    # {{{ variables view
    "variables": "selectable",
    "variable separator": "background",

    "var value": "sidebar one",
    "var label": "sidebar two",
    "focused var value": "focused sidebar one",
    "focused var label": "focused sidebar two",

    "highlighted var label": "highlighted",
    "highlighted var value": "highlighted",
    "focused highlighted var label": "focused var label",
    "focused highlighted var value": "focused var value",

    "return label": "var label",
    "return value": "var value",
    "focused return label": "focused var label",
    "focused return value": "focused var value",
    # }}}

    # {{{ stack
    "stack": "selectable",

    "frame name": "sidebar one",
    "frame class": "sidebar two",
    "frame location": "sidebar three",

    "focused frame name": "focused sidebar one",
    "focused frame class": "focused sidebar two",
    "focused frame location": "focused sidebar three",

    "current frame name": "frame name",
    "current frame class": "frame class",
    "current frame location": "frame location",

    "focused current frame name": "focused frame name",
    "focused current frame class": "focused frame class",
    "focused current frame location": "focused frame location",
    # }}}

    # {{{ breakpoints view
    "breakpoint": "sidebar two",
    "disabled breakpoint": "sidebar three",

    "current breakpoint": "breakpoint",
    "disabled current breakpoint": "disabled breakpoint",

    "focused breakpoint": "focused sidebar two",
    "focused current breakpoint": "focused breakpoint",

    "focused disabled breakpoint": "focused sidebar three",
    "focused disabled current breakpoint": "focused disabled breakpoint",
    # }}}

    # {{{ shell
    "command line edit": "source",
    "command line output": "source",
    "command line prompt": "source",
    "command line input": "source",
    "command line error": "warning",

    "focused command line output": "focused source",
    "focused command line input": "focused source",
    "focused command line error": "focused source",

    "command line clear button": "button",
    "command line focused button": "focused button",
    # }}}

    # {{{ Code syntax
    "comment":      "source",
    "keyword":      "source",
    "literal":      "source",
    "name":         "source",
    "operator":     "source",
    "punctuation":  "source",
    "argument":     "name",
    "builtin":      "name",
    "exception":    "name",
    "function":     "name",
    "pseudo":       "builtin",
    "class":        "function",
    "dunder":       "function",
    "magic":        "dunder",
    "namespace":    "keyword",
    "keyword2":     "keyword",
    "string":       "literal",
    "doublestring": "string",
    "singlestring": "string",
    "docstring":    "string",
    "backtick":     "string",
    # }}}
}
INHERITANCE_MAP = CLEAN_INHERITANCE_MAP.copy()


def get_style(palette_dict: dict, style_name: str):
    """
    Recursively search up the style hierarchy for the first style which has
    been defined, and add it to the palette_dict under the given style_name.
    """
    try:
        style = palette_dict[style_name]
        if not isinstance(style, PaletteEntry):
            style = PaletteEntry(style_name, *style)
            style.handle_256_colors()
            palette_dict[style_name] = style
        return style
    except KeyError:
        parent_name = INHERITANCE_MAP[style_name]
        style = replace(get_style(palette_dict, parent_name), name=style_name)
        palette_dict[style_name] = style
        return style


def link(child: str, parent: str):
    INHERITANCE_MAP[child] = parent

# }}}


def get_palette(may_use_fancy_formats: bool, theme: str = "classic") -> list:
    """
    Load the requested theme and return a list containing all palette entries
    needed to highlight the debugger UI, including syntax highlighting.
    """
    # undo previous link() calls
    INHERITANCE_MAP.update(CLEAN_INHERITANCE_MAP)

    if may_use_fancy_formats:
        def add_setting(color, setting):
            return f"{color}, {setting}"
    else:
        def add_setting(color, setting):
            return color

    # {{{ themes

    # {{{ base styles
    palette_dict = {
        "background": ("black", "light gray", "standout"),
        "selectable": ("black", "dark cyan", "bold"),
        "focused selectable": ("black", "dark green", "underline"),
        "input": (add_setting("yellow", "bold"), "dark blue"),
        "warning": (add_setting("white", "bold"), "dark red", "bold, standout"),
        "highlighted": ("white", "dark cyan", "bold, underline"),
        "source": ("white", "dark blue"),
    }
    # }}}

    if theme == "classic":
        # {{{ classic theme
        palette_dict.update({
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
            # }}}

            # {{{ highlighting

            "current line marker": ("dark red", "dark blue"),
            "breakpoint marker": ("dark red", "dark blue"),
            "line number": ("light gray", "dark blue"),
            "keyword": (add_setting("white", "bold"), "dark blue"),
            "function": ("light cyan", "dark blue"),
            "literal": ("light magenta, bold", "dark blue"),

            "string": (add_setting("light magenta", "bold"), "dark blue"),
            "doublestring": (add_setting("light magenta", "bold"), "dark blue"),
            "singlestring": (add_setting("light magenta", "bold"), "dark blue"),
            "docstring": (add_setting("light magenta", "bold"), "dark blue"),

            "punctuation": ("light gray", "dark blue"),
            "comment": ("light gray", "dark blue"),

            # }}}

            # {{{ breakpoints

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
        })
        # }}}
    elif theme == "vim":
        # {{{ vim theme

        palette_dict.update({
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

            "focused source": ("black", "dark green"),
            "highlighted source": ("black", "dark magenta"),
            "current source": ("black", "dark cyan"),
            "current focused source": (add_setting("white", "bold"), "dark cyan"),
            "current highlighted source": ("white", "dark cyan"),
            # }}}

            # {{{ breakpoints
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

            # {{{ syntax
            "source": ("black", "white"),
            "keyword": ("brown", "white"),

            "literal": ("black", "white"),
            "string": ("dark red", "white"),
            "doublestring": ("dark red", "white"),
            "singlestring": ("dark red", "white"),
            "docstring": ("dark red", "white"),

            "punctuation": ("black", "white"),
            "comment": ("dark blue", "white"),
            "function": ("dark cyan", "white"),
            "line number": ("dark gray", "white"),
            "current line marker": ("dark red", "white"),
            "breakpoint marker": ("dark red", "white"),
            # }}}

            # {{{ shell
            "command line edit":
            ("black", "white"),
            "command line prompt":
            (add_setting("black", "bold"), "white"),

            "command line output":
            (add_setting("black", "bold"), "white"),
            "command line input":
            ("black", "white"),
            "command line error":
            (add_setting("light red", "bold"), "white"),

            "focused command line output":
            ("black", "dark green"),
            "focused command line input":
            (add_setting("light cyan", "bold"), "dark green"),
            "focused command line error":
            ("black", "dark green"),

            "focused command line error": ("black", "dark green"),
            "command line clear button":
            (add_setting("white", "bold"), "dark blue"),
            "command line focused button": ("light cyan", "black"),
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

            "current line marker": ("dark red", "black"),
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

            "function": ("light cyan", "black"),
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
            "variables": ("white", "black"),

            "var label": ("light blue", "black"),
            "var value": ("white", "black"),

            "stack": ("white", "black"),

            "frame name": ("white", "black"),
            "frame class": ("dark blue", "black"),
            "frame location": ("light cyan", "black"),

            "current frame name": (add_setting("white", "bold"), "black"),
            "current frame class": ("dark blue", "black"),
            "current frame location": ("light cyan", "black"),

            "focused frame name": ("black", "dark green"),
            "focused frame class": (add_setting("white", "bold"), "dark green"),
            "focused frame location": ("dark blue", "dark green"),

            "focused current frame name": ("black", "dark green"),
            "focused current frame class": (
                add_setting("white", "bold"), "dark green"),
            "focused current frame location": ("dark blue", "dark green"),

            "search box": ("white", "black"),

            "breakpoint": ("white", "black"),
            "disabled breakpoint": ("dark gray", "black"),
            "focused breakpoint": ("black", "dark green"),
            "focused disabled breakpoint": ("dark gray", "dark green"),
            "current breakpoint": (add_setting("white", "bold"), "black"),
            "disabled current breakpoint": (
                add_setting("dark gray", "bold"), "black"),
            "focused current breakpoint": (
                add_setting("white", "bold"), "dark green", "bold"),
            "focused disabled current breakpoint": (
                add_setting("dark gray", "bold"), "dark green", "bold"),

            "source": ("white", "black"),
            "highlighted source": ("white", "light cyan"),
            "current source": ("white", "light gray"),
            "current focused source": ("white", "brown"),

            "line number": ("light gray", "black"),
            "keyword": ("dark magenta", "black"),
            "function": ("white", "black"),
            "literal": ("dark cyan", "black"),
            "string": ("dark red", "black"),
            "doublestring": ("dark red", "black"),
            "singlestring": ("light blue", "black"),
            "docstring": ("light red", "black"),
            "backtick": ("light green", "black"),
            "punctuation": ("white", "black"),
            "comment": ("dark green", "black"),

            "current line marker": ("dark red", "black"),
            "breakpoint marker": ("dark red", "black"),

            # {{{ shell

            "command line edit": ("white", "black"),
            "command line prompt": (add_setting("white", "bold"), "black"),

            "command line output": (add_setting("white", "bold"), "black"),
            "command line input": (add_setting("white", "bold"), "black"),
            "command line error": (add_setting("light red", "bold"), "black"),

            "focused command line output": ("black", "dark green"),
            "focused command line input": (
                    add_setting("white", "bold"), "dark green"),
            "focused command line error": ("black", "dark green"),

            "command line clear button": (add_setting("white", "bold"), "black"),
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

            "variables": ("light blue", "white"),

            "var label": ("dark blue", "white"),
            "var value": ("light blue", "white"),

            "focused var label": ("white", "dark blue"),
            "focused var value": ("black", "dark blue"),

            "highlighted var label": ("white", "light green"),
            "highlighted var value": ("white", "light green"),
            "focused highlighted var label": ("white", "light green"),
            "focused highlighted var value": ("white", "light green"),

            "stack": ("light blue", "white"),

            "frame name": ("dark blue", "white"),
            "frame class": ("light blue", "white"),
            "frame location": ("light green", "white"),

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
            "breakpoint": ("light blue", "white"),
            "disabled breakpoint": ("light gray", "white"),
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
            "current line marker": ("dark red", "white"),
            "breakpoint marker": ("dark red", "white"),

            "search box": ("white", "black"),

            "source": ("light blue", "white"),
            "current source": ("light gray", "light blue"),
            "current focused source": ("light gray", "light blue"),

            "focused source": ("dark gray", "dark blue"),

            "current highlighted source": ("black", "dark cyan"),
            "highlighted source": ("light blue", "black"),

            "line number": ("light blue", "white"),
            "keyword": ("dark green", "white"),
            "function": ("light blue", "white"),
            "literal": ("dark cyan", "white"),
            "string": ("dark cyan", "white"),
            "doublestring": ("dark cyan", "white"),
            "singlestring": ("light blue", "white"),
            "docstring": ("dark cyan", "white"),
            "backtick": ("light green", "white"),
            "punctuation": ("light blue", "white"),
            "comment": ("light green", "white"),

            # shell

            "command line edit": ("light blue", "white"),
            "command line prompt": ("light blue", "white"),

            "command line output": ("light blue", "white"),
            "command line input": ("light blue", "white"),
            "command line error": ("dark red", "white"),

            "focused command line output": ("black", "light green"),
            "focused command line input": ("black", "light green"),
            "focused command line error": ("dark red", "light blue"),

            "command line clear button": ("light blue", "white"),
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
            "current line marker": ("h160", "h235"),
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

            "function": ("h192", "h235"),
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
            "variables": ("white", "black"),

            "var label": ("light blue", "black"),
            "var value": ("white", "black"),

            "stack": ("white", "black"),

            "frame name": ("white", "black"),
            "frame class": ("dark blue", "black"),
            "frame location": ("light cyan", "black"),

            "current frame name": (add_setting("white", "bold"), "black"),
            "current frame class": ("dark blue", "black"),
            "current frame location": ("light cyan", "black"),

            "focused frame name": ("black", "dark green"),
            "focused frame class": (add_setting("white", "bold"), "dark green"),
            "focused frame location": ("dark blue", "dark green"),

            "focused current frame name": ("black", "dark green"),
            "focused current frame class": (
                add_setting("white", "bold"), "dark green"),
            "focused current frame location": ("dark blue", "dark green"),

            "search box": ("white", "black"),

            "breakpoint": ("white", "black"),
            "disabled breakpoint": ("dark gray", "black"),
            "focused breakpoint": ("black", "dark green"),
            "focused disabled breakpoint": ("dark gray", "dark green"),
            "current breakpoint": (add_setting("white", "bold"), "black"),
            "disabled current breakpoint": (
                add_setting("dark gray", "bold"), "black"),
            "focused current breakpoint": (
                add_setting("white", "bold"), "dark green", "bold"),
            "focused disabled current breakpoint": (
                add_setting("dark gray", "bold"), "dark green", "bold"),

            "source": ("white", "black"),
            "highlighted source": ("white", "light cyan"),
            "current source": ("white", "light gray"),
            "current focused source": ("white", "brown"),

            "line number": ("dark gray", "black"),
            "keyword2": ("light cyan", "black"),
            "function": ("light green", "black"),
            "literal": ("light magenta", "black"),

            "namespace": ("light red", "black"),
            "operator": ("light red", "black"),
            "argument": ("brown", "black"),
            "builtin": ("light cyan", "black"),
            "pseudo": ("light magenta", "black"),
            "dunder": ("light cyan", "black"),
            "exception": ("light cyan", "black"),
            "keyword": ("light red", "black"),

            "string": ("dark red", "black"),
            "doublestring": ("dark red", "black"),
            "singlestring": ("light blue", "black"),
            "docstring": ("light red", "black"),
            "backtick": ("light green", "black"),
            "punctuation": ("white", "black"),
            "comment": ("dark green", "black"),

            "current line marker": ("dark red", "black"),
            "breakpoint marker": ("dark red", "black"),

            # {{{ shell

            "command line edit": ("white", "black"),
            "command line prompt": (add_setting("white", "bold"), "black"),

            "command line output": (add_setting("white", "bold"), "black"),
            "command line input": (add_setting("white", "bold"), "black"),
            "command line error": (add_setting("light red", "bold"), "black"),

            "focused command line output": ("black", "dark green"),
            "focused command line input": (
                    add_setting("white", "bold"), "dark green"),
            "focused command line error": ("black", "dark green"),

            "command line clear button": (add_setting("white", "bold"), "black"),
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
            "current line marker": ("h160", "h235"),
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
            "function": ("h155", "h235"),
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
    elif theme == "mono":
        # {{{ mono
        palette_dict = {
            "background": ("standout",),
            "selectable": (),
            "focused selectable": ("underline",),
            "warning": ("bold",),
            "highlighted": ("bold",),
            "hotkey": ("underline, standout",),
        }
        # }}}
    else:
        # {{{ custom
        try:
            symbols = {
                "palette": palette_dict,
                "add_setting": add_setting,
                "link": link,
            }

            from os.path import expanduser, expandvars
            fname = expanduser(expandvars(theme))
            with open(fname) as inf:
                exec(compile(inf.read(), fname, "exec"), symbols)
        except FileNotFoundError:
            ui_log.error("Unable to locate custom theme file {!r}"
                         .format(theme))
            return None
        except Exception:
            ui_log.exception("Error when importing theme:")
            return None
        # }}}

    # }}}

    # Apply style inheritance
    for style_name in set(INHERITANCE_MAP.keys()).union(BASE_STYLES.keys()):
        get_style(palette_dict, style_name)

    palette_list = [
        astuple(entry)
        for entry in palette_dict.values()
        if isinstance(entry, PaletteEntry)
    ]

    return palette_list

# vim: foldmethod=marker
