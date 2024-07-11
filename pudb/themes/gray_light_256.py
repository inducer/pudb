from pudb.themes.utils import add_setting


palette_dict = {
    # {{{ base styles
    "background": ("h232", "h248"),
    "selectable": ("h232", "h252"),
    "focused selectable": ("h232", "h251"),
    "highlighted": (add_setting("h234", "bold, underline"), "h252"),
    "hotkey": (add_setting("h232", "underline"), "h248"),
    # }}}
    # {{{ general ui
    "focused sidebar": (add_setting("h232", "bold"), "h248"),
    "warning": (add_setting("h232", "bold"), "h253"),
    "group head": (add_setting("h232", "bold"), "h248"),
    "dialog title": (add_setting("h232", "underline, bold"), "h248"),
    # }}}
    # {{{ source view
    "source": ("h235", "h253"),
    "current source": (add_setting("h232", "underline"), "h253"),
    "line number": ("h244", "h253"),
    # }}}
    # {{{ sidebar
    "sidebar two": (add_setting("h234", "bold"), "h252"),
    "focused sidebar two": (add_setting("h234", "bold"), "h251"),
    "sidebar three": ("h239", "h252"),
    "focused sidebar three": ("h239", "h251"),
    # }}}
    # {{{ Code syntax
    "exception":   (add_setting("h236", "underline"), "h253"),
    "class":       (add_setting("h234", "bold, underline"), "h253"),
    "keyword":     (add_setting("h234", "bold"), "h253"),
    "comment":     ("h244", "h253"),
    # }}}
}
