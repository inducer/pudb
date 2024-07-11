from pudb.themes.utils import add_setting


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
    "current line marker": (add_setting("light blue", "bold"), "white"),
    "breakpoint marker": (add_setting("light red", "bold"), "white"),
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
    "current frame name": (add_setting("light green", "bold"), "white"),
    "focused current frame name": (add_setting("white", "bold"), "dark blue"),
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

# vim: foldmethod=marker
