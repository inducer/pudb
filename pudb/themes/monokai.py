from pudb.themes.utils import add_setting, link


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
    "focused command line error": (add_setting("yellow", "bold"), "dark gray"),
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

# vim: foldmethod=marker
