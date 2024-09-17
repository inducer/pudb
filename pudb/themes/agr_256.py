from pudb.themes.utils import add_setting, link


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
    "focused return label": (add_setting(light_gray, "bold"), dark_cyan),
    # }}}
    # {{{ stack
    "current frame name": (yellow, blacker),
    "focused current frame name": (add_setting(yellow, "bold"), dark_cyan),
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

# vim: foldmethod=marker
