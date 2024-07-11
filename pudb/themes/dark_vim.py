from pudb.themes.utils import add_setting, link


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

# vim: foldmethod=marker
