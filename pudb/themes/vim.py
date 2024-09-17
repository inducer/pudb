from pudb.themes.utils import add_setting, link


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
    "current frame name": (add_setting("white", "bold"), "dark cyan"),
    "focused current frame name": (add_setting("black", "bold"), "light cyan"),
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

# vim: foldmethod=marker
