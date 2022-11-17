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
    "nord-256",
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
INHERITANCE_MAP = {
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
    "header warning": "warning",
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


def get_style(palette_dict: dict, style_name: str,
              inheritance_overrides: dict) -> dict:
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
        parent_name = inheritance_overrides.get(
            style_name,
            INHERITANCE_MAP[style_name],
        )
        style = replace(
            get_style(palette_dict, parent_name, inheritance_overrides),
            name=style_name
        )
        palette_dict[style_name] = style
        return style

# }}}


def get_palette(may_use_fancy_formats: bool, theme: str = "classic") -> list:
    """
    Load the requested theme and return a list containing all palette entries
    needed to highlight the debugger UI, including syntax highlighting.
    """
    inheritance_overrides = {}

    if may_use_fancy_formats:
        def add_setting(color, setting):
            return f"{color}, {setting}"
    else:
        def add_setting(color, setting):
            return color

    def link(child: str, parent: str):
        inheritance_overrides[child] = parent

    # {{{ themes

    if theme == "classic":
        # {{{ classic theme
        link("current breakpoint", "current frame name")
        link("focused current breakpoint", "focused current frame name")

        palette_dict = {
            # {{{ base styles
            "background": ("black", "light gray"),
            "selectable": ("black", "dark cyan"),
            "focused selectable": ("black", "light cyan"),
            "highlighted": ("dark blue", "yellow"),
            "hotkey": (add_setting("black", "underline"), "light gray"),
            # }}}
            # {{{ general ui
            "header": ("dark blue", "light gray"),
            "dialog title": (add_setting("white", "bold"), "dark blue"),
            "warning": (add_setting("white", "bold"), "dark red"),
            # }}}
            # {{{ source view
            "source": ("yellow", "dark blue"),
            "current source": ("dark blue", "dark green"),
            "breakpoint source": (
                add_setting("yellow", "bold"), "dark red"),
            "line number": ("light gray", "dark blue"),
            "breakpoint marker": (
                add_setting("dark red", "bold"), "dark blue"),
            # }}}
            # {{{ sidebar
            "sidebar two": ("dark blue", "dark cyan"),
            "sidebar three": ("dark gray", "dark cyan"),
            "focused sidebar two": ("dark blue", "light cyan"),
            "focused sidebar three": ("dark gray", "light cyan"),
            # }}}
            # {{{ variables view
            "return label": ("white", "dark blue"),
            "focused return label": ("light gray", "dark blue"),
            # }}}
            # {{{ stack
            "current frame name": (
                add_setting("white", "bold"), "dark cyan"),
            "focused current frame name": (
                add_setting("black", "bold"), "light cyan"),
            # }}}
            # {{{ shell
            "command line output": ("light cyan", "dark blue"),
            "command line prompt": (
                add_setting("white", "bold"), "dark blue"),
            "command line error": (
                add_setting("light green", "bold"), "dark blue"),
            "command line clear button": (
                add_setting("white", "bold"), "dark blue"),
            "command line focused button": ("dark blue", "dark cyan"),
            # }}}
            # {{{ Code syntax
            "keyword": (add_setting("white", "bold"), "dark blue"),
            "function": ("light cyan", "dark blue"),
            "literal": (add_setting("light green", "bold"), "dark blue"),
            "punctuation": ("light gray", "dark blue"),
            "comment": ("dark cyan", "dark blue"),
            # }}}
        }
        # }}}
    elif theme == "vim":
        # {{{ vim theme
        link("current breakpoint", "current frame name")
        link("focused current breakpoint", "focused current frame name")

        palette_dict = {
            # {{{ base styles
            "background": ("black", "light gray"),
            "selectable": ("black", "dark cyan"),
            "focused selectable": ("black", "light cyan"),
            "hotkey": (add_setting("black", "bold, underline"), "light gray"),
            "highlighted": ("black", "yellow"),
            # }}}
            # {{{ general ui
            "header": (add_setting("black", "bold"), "light gray"),
            "group head": ("dark blue", "light gray"),
            "dialog title": (add_setting("white", "bold"), "dark blue"),
            "input": ("black", "dark cyan"),
            "focused input": ("black", "light cyan"),
            "warning": (add_setting("dark red", "bold"), "white"),
            "header warning": (add_setting("dark red", "bold"), "light gray"),
            # }}}
            # {{{ source view
            "source": ("black", "white"),
            "current source": ("black", "dark cyan"),
            "breakpoint source": ("dark red", "light gray"),
            "line number": ("dark gray", "white"),
            "current line marker": ("dark red", "white"),
            "breakpoint marker": ("dark red", "white"),
            # }}}
            # {{{ sidebar
            "sidebar one": ("black", "dark cyan"),
            "sidebar two": ("dark blue", "dark cyan"),
            "sidebar three": ("dark gray", "dark cyan"),
            "focused sidebar one": ("black", "light cyan"),
            "focused sidebar two": ("dark blue", "light cyan"),
            "focused sidebar three": ("dark gray", "light cyan"),
            # }}}
            # {{{ variables view
            "highlighted var label": ("dark blue", "yellow"),
            "return label": ("white", "dark blue"),
            "focused return label": ("light gray", "dark blue"),
            # }}}
            # {{{ stack
            "current frame name": (
                add_setting("white", "bold"), "dark cyan"),
            "focused current frame name": (
                add_setting("black", "bold"), "light cyan"),
            # }}}
            # {{{ shell
            "command line output": (
                add_setting("dark gray", "bold"), "white"),
            # }}}
            # {{{ Code syntax
            "keyword2": ("dark magenta", "white"),
            "namespace": ("dark magenta", "white"),
            "literal": ("dark red", "white"),
            "exception": ("dark red", "white"),
            "comment": ("dark gray", "white"),
            "function": ("dark blue", "white"),
            "pseudo": ("dark gray", "white"),
            "builtin": ("light blue", "white"),
            # }}}
            }
        # }}}
    elif theme == "dark vim":
        # {{{ dark vim

        link("current breakpoint", "current frame name")
        link("focused current breakpoint", "focused current frame name")
        palette_dict = {
            # {{{ base styles
            "background": ("black", "light gray"),
            "selectable": ("white", "dark gray"),
            "focused selectable": (add_setting("white", "bold"), "light blue"),
            "highlighted": ("black", "dark green"),
            "hotkey": (add_setting("dark blue", "underline"), "light gray"),
            # }}}
            # {{{ general ui
            "header": ("dark blue", "light gray"),
            "dialog title": (add_setting("white", "bold"), "black"),
            "warning": (add_setting("light red", "bold"), "black"),
            "header warning": (add_setting("light red", "bold"), "light gray"),
            # }}}
            # {{{ source view
            "source": ("white", "black"),
            "current source": (add_setting("white", "bold"), "dark gray"),
            "line number": (add_setting("dark gray", "bold"), "black"),
            "breakpoint marker": (add_setting("light red", "bold"), "black"),
            "breakpoint source": (add_setting("white", "bold"), "dark red"),
            # }}}
            # {{{ sidebar
            "sidebar two": ("yellow", "dark gray"),
            "focused sidebar two": ("light cyan", "light blue"),
            "sidebar three": ("light gray", "dark gray"),
            "focused sidebar three": ("yellow", "light blue"),
            # }}}
            # {{{ stack
            "current frame name": (
                add_setting("white", "bold"), "dark gray"),
            # }}}
            # {{{ shell
            "command line output": (add_setting("yellow", "bold"), "black"),
            # }}}
            # {{{ Code syntax
            "keyword": ("yellow", "black"),
            "literal": ("light magenta", "black"),
            "function": (add_setting("light cyan", "bold"), "black"),
            "punctuation": ("yellow", "black"),
            "comment": ("dark cyan", "black"),
            "exception": ("light red", "black"),
            "builtin": ("light green", "black"),
            "pseudo": ("dark green", "black"),
            # }}}
            }
        # }}}
    elif theme == "midnight":
        # {{{ midnight

        # Based on XCode's midnight theme
        # Looks best in a console with green text against black background
        link("current breakpoint", "current frame name")
        link("focused current breakpoint", "focused current frame name")
        palette_dict = {
            # {{{ base styles
            "background": ("black", "light gray"),
            "selectable": ("white", "black"),
            "focused selectable": ("white", "dark blue"),
            "hotkey": (add_setting("black", "underline, italics"), "light gray"),
            "highlighted": ("black", "dark green"),
            # }}}
            # {{{ general ui
            "input": ("light green", "black"),
            "focused input": ("light green", "black"),
            "warning": (add_setting("white", "bold"), "dark red"),
            "dialog title": (add_setting("white", "bold"), "dark blue"),
            "group head": (add_setting("dark blue", "bold"), "light gray"),
            "button": (add_setting("white", "bold"), "dark blue"),
            "focused button": ("white", "black"),
            "focused sidebar": ("black", "white"),
            "value": (add_setting("yellow", "bold"), "dark blue"),
            # }}}
            # {{{ source view
            "source": ("light green", "black"),
            "highlighted source": ("black", "dark green"),
            "current source": ("black", "brown"),
            "current focused source": (add_setting("yellow", "bold"), "dark blue"),
            "breakpoint source": (add_setting("yellow", "bold"), "dark red"),
            "current breakpoint source": ("black", "dark red"),

            "line number": ("light gray", "black"),
            "current line marker": ("dark red", "black"),
            "breakpoint marker": ("dark red", "black"),
            # }}}
            # {{{ sidebar
            "sidebar two": ("light blue", "black"),
            "sidebar three": ("light cyan", "black"),
            # }}}
            # {{{ variables view
            "return label": ("white", "dark blue"),
            "return value": ("black", "dark cyan"),
            "focused return label": ("light gray", "dark blue"),
            # }}}
            # {{{ stack
            "current frame name": (add_setting("white", "bold"), "black"),
            "current frame class": (add_setting("light blue", "bold"), "black"),
            "current frame location": (add_setting("light cyan", "bold"), "black"),

            "focused current frame name": (
                add_setting("white", "bold"), "dark blue"),
            "focused current frame class": (
                add_setting("white", "bold"), "dark blue"),
            "focused current frame location": (
                add_setting("white", "bold"), "dark blue"),
            # }}}
            # {{{ breakpoints view
            "breakpoint": ("white", "black"),
            "disabled breakpoint": ("dark gray", "black"),
            "focused disabled breakpoint": ("light gray", "dark blue"),
            "current breakpoint": (add_setting("white", "bold"), "black"),
            "disabled current breakpoint": (
                add_setting("dark gray", "bold"), "black"),
            "focused current breakpoint": (
                add_setting("white", "bold"), "dark blue"),
            "focused disabled current breakpoint": (
                add_setting("light gray", "bold"), "dark blue"),
            # }}}
            # {{{ shell
            "command line edit": ("white", "black"),
            "command line prompt": (add_setting("white", "bold"), "black"),

            "command line input": ("white", "black"),
            "command line error": (add_setting("light red", "bold"), "black"),

            "command line clear button": (add_setting("white", "bold"), "black"),
            "command line focused button": ("white", "dark blue"),
            # }}}
            # {{{ Code syntax
            "keyword": ("dark magenta", "black"),
            "operator": ("dark green", "black"),
            "pseudo": ("light magenta", "black"),
            "function": (add_setting("light blue", "bold"), "black"),
            "builtin": ("dark gray", "black"),
            "literal": ("dark cyan", "black"),
            "string": ("dark red", "black"),
            "docstring": ("yellow", "black"),
            "backtick": ("dark green", "black"),
            "punctuation": ("white", "black"),
            "comment": ("white", "black"),
            "exception": ("dark green", "black"),
            # }}}
        }

        # }}}
    elif theme == "solarized":
        # {{{ solarized
        palette_dict = {
            # {{{ base styles
            "background": ("light green", "light gray"),
            "selectable": ("light green", "white"),
            "focused selectable": ("white", "dark blue"),
            "highlighted": ("white", "dark cyan"),
            "hotkey": (add_setting("black", "underline"), "light gray"),
            # }}}
            # {{{ general ui
            "dialog title": (add_setting("white", "bold"), "dark cyan"),
            "warning": (add_setting("light red", "bold"), "white"),
            "header warning": (add_setting("light red", "bold"), "light gray"),
            "focused sidebar": ("dark red", "light gray"),
            "group head": (add_setting("yellow", "bold"), "light gray"),
            # }}}
            # {{{ source view
            "source": ("yellow", "white"),
            "breakpoint source": ("light red", "light gray"),
            "current source": ("light gray", "light blue"),
            "line number": ("light blue", "white"),
            "current line marker": (
                add_setting("light blue", "bold"), "white"),
            "breakpoint marker": (
                add_setting("light red", "bold"), "white"),
            # }}}
            # {{{ sidebar
            "sidebar two": ("dark blue", "white"),
            "sidebar three": ("light cyan", "white"),
            "focused sidebar three": ("light gray", "dark blue"),
            # }}}
            # {{{ variables view
            "return label": ("white", "yellow"),
            "focused return label": ("white", "yellow"),
            # }}}
            # {{{ stack
            "current frame name": (
                add_setting("light green", "bold"), "white"),
            "focused current frame name": (
                add_setting("white", "bold"), "dark blue"),
            # }}}
            # {{{ shell
            "command line output": ("light green", "white"),
            # }}}
            # {{{ Code syntax
            "namespace": ("dark red", "white"),
            "exception": ("light red", "white"),
            "keyword": ("brown", "white"),
            "keyword2": ("dark magenta", "white"),
            "function": ("dark green", "white"),
            "literal": ("dark cyan", "white"),
            "builtin": ("dark blue", "white"),
            "comment": ("light cyan", "white"),
            "pseudo": ("light cyan", "white"),
            # }}}
        }

    # }}}
    elif theme == "agr-256":
        # {{{ agr-256

        # Give the colors some comprehensible names
        black = "h235"
        blacker = "h233"
        dark_cyan = "h24"
        dark_gray = "h241"
        dark_green = "h22"
        dark_red = "h88"
        dark_teal = "h23"
        light_blue = "h111"
        light_cyan = "h80"
        light_gray = "h252"
        light_green = "h113"
        light_red = "h160"
        medium_gray = "h246"
        salmon = "h223"
        orange = "h173"
        white = "h255"
        yellow = "h192"

        link("focused breakpoint", "focused selectable")
        link("current breakpoint", "current frame name")
        link("focused current breakpoint", "focused current frame name")
        palette_dict = {
            # {{{ base styles
            "background": (black, light_gray),
            "selectable": (white, blacker),
            "focused selectable": (yellow, dark_cyan),
            "hotkey": (add_setting(black, "underline"), light_gray),
            "highlighted": (white, dark_green),
            # }}}
            # {{{ general ui
            "focused sidebar": (dark_cyan, light_gray),
            "group head": (add_setting(dark_cyan, "bold"), light_gray),
            "dialog title": (add_setting(light_gray, "bold"), black),
            "warning": (add_setting(white, "bold"), dark_red),
            "fixed value": (add_setting(white, "bold"), dark_gray),
            "button": (add_setting(white, "bold"), black),
            "focused button": (add_setting(yellow, "bold"), dark_cyan),
            # }}}
            # {{{ source view
            "line number": (dark_gray, black),
            "current line marker": (add_setting(yellow, "bold"), black),
            "breakpoint marker": (add_setting(light_red, "bold"), black),
            "source": (white, black),
            "breakpoint source": (add_setting(white, "bold"), dark_red),
            "current source": (add_setting(light_gray, "bold"), dark_teal),
            # }}}
            # {{{ sidebar
            "sidebar two": (light_blue, blacker),
            "focused sidebar two": (light_gray, dark_cyan),
            "sidebar three": (medium_gray, blacker),
            "focused sidebar three": (salmon, dark_cyan),
            # }}}
            # {{{ variables view
            "highlighted var label": (light_gray, dark_green),
            "return label": (light_green, blacker),
            "focused return label": (
                add_setting(light_gray, "bold"), dark_cyan),
            # }}}
            # {{{ stack
            "current frame name": (yellow, blacker),
            "focused current frame name": (
                add_setting(yellow, "bold"), dark_cyan),
            # }}}
            # {{{ shell
            "command line prompt": (add_setting(yellow, "bold"), black),
            "command line output": (light_cyan, black),
            "command line error": (light_red, black),
            # }}}
            # {{{ Code syntax
            "comment": (medium_gray, black),
            "exception": (orange, black),
            "function": (yellow, black),
            "keyword": (light_blue, black),
            "literal": (orange, black),
            "operator": (yellow, black),
            "pseudo": (medium_gray, black),
            "punctuation": (salmon, black),
            "string": (light_green, black),
            # }}}
        }
        # }}}
    elif theme == "monokai":
        # {{{ monokai
        link("current breakpoint", "current frame name")
        link("focused current breakpoint", "focused current frame name")
        palette_dict = {
            # {{{ base styles
            "background": ("black", "light gray"),
            "selectable": ("white", "black"),
            "focused selectable": ("white", "dark gray"),
            "highlighted": ("black", "dark green"),
            "hotkey": (add_setting("black", "underline"), "light gray"),
            # }}}
            # {{{ general ui
            "input": ("white", "black"),
            "button": (add_setting("white", "bold"), "black"),
            "focused button": (add_setting("white", "bold"), "dark gray"),
            "focused sidebar": ("dark blue", "light gray"),
            "warning": (add_setting("white", "bold"), "dark red"),
            "group head": (add_setting("black", "bold"), "light gray"),
            "dialog title": (add_setting("white", "bold"), "black"),
            # }}}
            # {{{ source view
            "current source": ("black", "dark cyan"),
            "breakpoint source": (add_setting("white", "bold"), "dark red"),
            "line number": ("dark gray", "black"),
            "current line marker": (add_setting("dark cyan", "bold"), "black"),
            "breakpoint marker": (add_setting("dark red", "bold"), "black"),
            # }}}
            # {{{ sidebar
            "sidebar two": ("light cyan", "black"),
            "focused sidebar two": ("light cyan", "dark gray"),
            "sidebar three": ("light magenta", "black"),
            "focused sidebar three": ("light magenta", "dark gray"),
            # }}}
            # {{{ variables view
            "return label": ("light green", "black"),
            "focused return label": ("light green", "dark gray"),
            # }}}
            # {{{ stack
            "current frame name": ("light green", "black"),
            "focused current frame name": ("light green", "dark gray"),
            # }}}
            # {{{ shell
            "command line prompt": (add_setting("yellow", "bold"), "black"),
            "command line output": ("light cyan", "black"),
            "command line error": ("yellow", "black"),
            "focused command line output": ("light cyan", "dark gray"),
            "focused command line error": (
                add_setting("yellow", "bold"), "dark gray"),
            # }}}
            # {{{ Code syntax
            "literal":   ("light magenta", "black"),
            "builtin":   ("light cyan", "black"),
            "exception": ("light cyan", "black"),
            "keyword2":  ("light cyan", "black"),
            "function":  ("light green", "black"),
            "class":     (add_setting("light green", "underline"), "black"),
            "keyword":   ("light red", "black"),
            "operator":  ("light red", "black"),
            "comment":   ("dark gray", "black"),
            "docstring": ("dark gray", "black"),
            "argument":  ("brown", "black"),
            "pseudo":    ("brown", "black"),
            "string":    ("yellow", "black"),
            # }}}
        }

        # }}}
    elif theme == "monokai-256":
        # {{{ monokai-256

        # Give the colors some comprehensible names
        black = "h236"
        blacker = "h234"
        dark_gray = "h240"
        dark_green = "h28"
        dark_red = "h124"
        dark_teal = "h30"
        dark_magenta = "h141"
        light_blue = "h111"
        light_cyan = "h51"
        light_gray = "h252"
        light_green = "h155"
        light_red = "h160"
        light_magenta = "h198"
        medium_gray = "h243"
        orange = "h208"
        white = "h255"
        yellow = "h228"
        link("current breakpoint", "current frame name")
        link("focused current breakpoint", "focused current frame name")
        palette_dict = {

            # {{{ base styles
            "background": (black, light_gray),
            "selectable": (white, blacker),
            "focused selectable": (white, dark_gray),
            "highlighted": (white, dark_green),
            "hotkey": (add_setting(black, "underline"), light_gray),
            # }}}
            # {{{ general ui
            "input": (white, black),
            "button": (add_setting(white, "bold"), black),
            "focused button": (add_setting(white, "bold"), dark_gray),
            "focused sidebar": (dark_teal, light_gray),
            "warning": (add_setting(white, "bold"), dark_red),
            "group head": (add_setting(black, "bold"), light_gray),
            "dialog title": (add_setting(white, "bold"), blacker),
            # }}}
            # {{{ source view
            "source": (white, black),
            "current source": (add_setting(light_gray, "bold"), dark_teal),
            "breakpoint source": (add_setting(white, "bold"), dark_red),
            "line number": (dark_gray, black),
            "current line marker": (add_setting(light_cyan, "bold"), black),
            "breakpoint marker": (add_setting(light_red, "bold"), black),
            # }}}
            # {{{ sidebar
            "sidebar two": (light_cyan, blacker),
            "focused sidebar two": (light_cyan, dark_gray),
            "sidebar three": (dark_magenta, blacker),
            "focused sidebar three": (dark_magenta, dark_gray),
            # }}}
            # {{{ variables view
            "highlighted var label": (light_gray, dark_green),
            "return label": (light_green, blacker),
            "focused return label": (light_green, dark_gray),
            # }}}
            # {{{ stack
            "current frame name": (light_green, blacker),
            "focused current frame name": (light_green, dark_gray),
            # }}}
            # {{{ shell
            "command line prompt": (
                add_setting(yellow, "bold"), black),
            "command line output": (light_cyan, black),
            "command line error": (orange, black),
            "focused command line output": (light_cyan, dark_gray),
            "focused command line error": (
                add_setting(orange, "bold"), dark_gray),
            # }}}
            # {{{ Code syntax
            "literal":     (dark_magenta, black),
            "builtin":     (light_cyan, black),
            "exception":   (light_cyan, black),
            "keyword2":    (light_cyan, black),
            "function":    (light_green, black),
            "class":       (add_setting(light_green, "underline"), black),
            "keyword":     (light_magenta, black),
            "operator":    (light_magenta, black),
            "comment":     (medium_gray, black),
            "docstring":   (medium_gray, black),
            "argument":    (orange, black),
            "pseudo":      (orange, black),
            "string":      (yellow, black),
            # }}}
        }

        # }}}
    elif theme == "mono":
        # {{{ mono
        palette_dict = {
            "background": ("standout",),
            "selectable": (),
            "focused selectable": ("underline",),
            "highlighted": ("bold",),
            "hotkey": ("underline, standout",),
        }

        # }}}

    elif theme == "nord-256":
        # {{{ nord-256

        # ------------------------------------------------------------------------------
        # Colors are approximations of https://www.nordtheme.com/docs/colors-and-palettes
        # Polar Night is made up of four darker colors (nord 0, nord1, nord2, and nord3) 
        # that are commonly used for base elements like backgrounds or text color in 
        # bright ambiance designs.
        # ------------------------------------------------------------------------------

        # nord0 is the origin color or the Polar Night palette.
        nord0 = "h236"

        # nord1 is a brighter shade color based on nord0.
        nord1 = "h238"

        # nord2 is an even more brighter shade color of nord0.
        nord2 = "h239"

        # nord3 is the brightest shade color based on nord0.
        nord3 = "h240"

        # nord4 is the origin color or the Snow Storm palette.
        nord4 = "h253"

        # nord5 is a brighter shade color of nord4.
        nord5 = "h255"

        # nord6 is the brightest shade color based on nord4.
        # We don't use nord 6 because it is not representable.
        # nord6 = "h256"


        # nord7 is a calm and highly contrasted color reminiscent of
        # frozen polar water.
        nord7 = "h109"

        
        # nord8 is a bright and shiny primary accent color reminiscent of pure
        # and clear ice.
        nord8 = "h110"


        # nord9 is a more darkened and less saturated color reminiscent of
        # arctic waters.
        nord9 = "h109"

        # nord10 is a dark and intensive color reminiscent of the deep arctic ocean.
        nord10 = "h67"

        # nord11 is a reddish color.
        nord11 = "h131"

        link("current breakpoint", "current frame name")
        link("focused current breakpoint", "focused current frame name")
        palette_dict = {

            # {{{ base styles
            "background": (nord0, nord7),
            "selectable": (nord4, nord1),
            "focused selectable": (nord4, nord2),
            "highlighted": (nord4, nord3),
            "hotkey": (add_setting(nord0, "underline"), nord7),
            # }}}
            # {{{ general ui
            "input": (nord4, nord0),
            "button": (add_setting(nord4, "bold"), nord0),
            "focused button": (add_setting(nord4, "bold"), nord2),
            "focused sidebar": (nord0, nord11),
            "warning": (add_setting(nord4, "bold"), nord4),
            "group head": (add_setting(nord0, "bold"), nord1),
            "dialog title": (add_setting(nord4, "bold"), nord1),
            # }}}
            # {{{ source view
            "source": (nord4, nord0),
            "current source": (nord11, nord0),
            "breakpoint source": (nord4, nord0),
            "line number": (nord2, nord0),
            "current line marker": (add_setting(nord11, "bold"), nord0),
            "breakpoint marker": (add_setting(nord11, "bold"), nord0),
            # }}}
            # {{{ sidebar
            "sidebar two": (nord9, nord1),
            "focused sidebar two": (nord0, nord2),
            "sidebar three": (nord0, nord1),
            "focused sidebar three": (nord5, nord2),
            # }}}
            # {{{ variables view
            "highlighted var label": (nord8, nord9),
            "return label": (nord9, nord8),
            "focused return label": (nord9, nord8),
            # }}}
            # {{{ stack
            "current frame name": (nord9, nord1),
            "focused current frame name": (nord9, nord2),
            # }}}
            # {{{ shell
            "command line prompt": (
                add_setting(nord5, "bold"), nord0),
            "command line output": (nord7, nord0),
            "command line error": (nord3, nord0),
            "focused command line output": (nord7, nord2),
            "focused command line error": (
                add_setting(nord3, "bold"), nord2),
            # }}}
            # {{{ Code syntax
            "literal":     (nord8, nord0),
            "builtin":     (nord8, nord0),
            "exception":   (nord8, nord0),
            "keyword2":    (nord9, nord0),
            "function":    (nord8, nord0),
            "class":       (add_setting(nord9, "underline"), nord0),
            "keyword":     (nord8, nord0),
            "operator":    (nord5, nord0),
            "comment":     (nord2, nord0),
            "docstring":   (nord2, nord0),
            "argument":    (nord11, nord0),
            "pseudo":      (nord5, nord0),
            "string":      (nord5, nord0),
            # }}}
        }
        # }}}
    else:
        # {{{ custom
        try:
            # {{{ base styles
            palette_dict = {
                "background": ("black", "light gray"),
                "hotkey": (add_setting("black", "underline"), "light gray"),
                "selectable": ("black", "dark cyan"),
                "focused selectable": ("black", "dark green"),
                "input": (add_setting("yellow", "bold"), "dark blue"),
                "warning": (add_setting("white", "bold"), "dark red"),
                "highlighted": ("white", "dark cyan"),
                "source": ("white", "dark blue"),
            }
            # }}}

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
        get_style(palette_dict, style_name, inheritance_overrides)

    palette_list = [
        astuple(entry)
        for entry in palette_dict.values()
        if isinstance(entry, PaletteEntry)
    ]

    return palette_list

# vim: foldmethod=marker
