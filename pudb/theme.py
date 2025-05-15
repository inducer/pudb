from __future__ import annotations


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

from dataclasses import astuple, dataclass, replace

from pudb.lowlevel import ui_log
from pudb.themes import THEMES
from pudb.themes.utils import (
    add_setting,
    inheritance_overrides,
    link,
    reset_inheritance_overrides,
)


@dataclass
class PaletteEntry:
    name: str
    foreground: str = "default"
    background: str = "default"
    mono: str | None = None
    foreground_high: str | None = None
    background_high: str | None = None

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
    "background": None,
    "selectable": None,
    "focused selectable": None,
    "highlighted": None,
    "hotkey": None,
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


def set_style(palette_dict: dict, style_name: str,
              inheritance_overrides: dict) -> PaletteEntry:
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
            set_style(palette_dict, parent_name, inheritance_overrides),
            name=style_name
        )
        palette_dict[style_name] = style
        return style

# }}}


# {{{ get palette

def get_palette(may_use_fancy_formats: bool, theme: str = "classic") -> list:
    """
    Load the requested theme and return a list containing all palette entries
    needed to highlight the debugger UI, including syntax highlighting.
    """
    reset_inheritance_overrides()

    try:
        palette_dict = THEMES[theme]
    except KeyError:
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
            ui_log.error(f"Unable to locate custom theme file {theme!r}"
                         )
            return None
        except Exception:
            ui_log.exception("Error when importing theme:")
            return None
        # }}}

    # Apply style inheritance
    for style_name in set(INHERITANCE_MAP.keys()).union(BASE_STYLES.keys()):
        set_style(palette_dict, style_name, inheritance_overrides)

    palette_list = [
        astuple(entry)
        for entry in palette_dict.values()
        if isinstance(entry, PaletteEntry)
    ]

    return palette_list

# }}}

# vim: foldmethod=marker
