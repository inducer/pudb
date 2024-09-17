from pudb.themes.utils import add_setting, link


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
    "command line prompt": (add_setting(yellow, "bold"), black),
    "command line output": (light_cyan, black),
    "command line error": (orange, black),
    "focused command line output": (light_cyan, dark_gray),
    "focused command line error": (add_setting(orange, "bold"), dark_gray),
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

# vim: foldmethod=marker
