from pudb.themes.utils import add_setting, link


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

    "focused current frame name": (add_setting("white", "bold"), "dark blue"),
    "focused current frame class": (add_setting("white", "bold"), "dark blue"),
    "focused current frame location": (add_setting("white", "bold"), "dark blue"),
    # }}}
    # {{{ breakpoints view
    "breakpoint": ("white", "black"),
    "disabled breakpoint": ("dark gray", "black"),
    "focused disabled breakpoint": ("light gray", "dark blue"),
    "current breakpoint": (add_setting("white", "bold"), "black"),
    "disabled current breakpoint": (add_setting("dark gray", "bold"), "black"),
    "focused current breakpoint": (add_setting("white", "bold"), "dark blue"),
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

# vim: foldmethod=marker
