from pudb.themes.utils import add_setting, link


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
    "breakpoint source": (add_setting("yellow", "bold"), "dark red"),
    "line number": ("light gray", "dark blue"),
    "breakpoint marker": (add_setting("dark red", "bold"), "dark blue"),
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
    "current frame name": (add_setting("white", "bold"), "dark cyan"),
    "focused current frame name": (add_setting("black", "bold"), "light cyan"),
    # }}}
    # {{{ shell
    "command line output": ("light cyan", "dark blue"),
    "command line prompt": (add_setting("white", "bold"), "dark blue"),
    "command line error": (add_setting("light green", "bold"), "dark blue"),
    "command line clear button": (add_setting("white", "bold"), "dark blue"),
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

# vim: foldmethod=marker
