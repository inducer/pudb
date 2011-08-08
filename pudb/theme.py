THEMES = ["classic", "vim", "dark vim", "midnight"]




def get_palette(may_use_fancy_formats, theme="classic"):
    if may_use_fancy_formats:
        def add_setting(color, setting):
            return color+","+setting
    else:
        def add_setting(color, setting):
            return color

    palette = [
        ("header", "black", "light gray", "standout"),

        ("breakpoint source", "yellow", "dark red"),
        ("breakpoint focused source", "black", "dark red"),
        ("current breakpoint source", "black", "dark red"),
        ("current breakpoint focused source", "white", "dark red"),

        ("variables", "black", "dark cyan"),
        ("variable separator", "dark cyan", "light gray"),

        ("var label", "dark blue", "dark cyan"),
        ("var value", "black", "dark cyan"),
        ("focused var label", "dark blue", "dark green"),
        ("focused var value", "black", "dark green"),

        ("highlighted var label", "white", "dark cyan"),
        ("highlighted var value", "black", "dark cyan"),
        ("focused highlighted var label", "white", "dark green"),
        ("focused highlighted var value", "black", "dark green"),

        ("return label", "white", "dark blue"),
        ("return value", "black", "dark cyan"),
        ("focused return label", "light gray", "dark blue"),
        ("focused return value", "black", "dark green"),

        ("return label", "white", "dark blue"),
        ("return value", "black", "dark cyan"),
        ("focused return label", "light gray", "dark blue"),
        ("focused return value", "black", "dark green"),

        ("stack", "black", "dark cyan"),

        ("frame name", "black", "dark cyan"),
        ("focused frame name", "black", "dark green"),
        ("frame class", "dark blue", "dark cyan"),
        ("focused frame class", "dark blue", "dark green"),
        ("frame location", "light cyan", "dark cyan"),
        ("focused frame location", "light cyan", "dark green"),

        ("current frame name", add_setting("white", "bold"),
            "dark cyan"),
        ("focused current frame name", add_setting("white", "bold"),
            "dark green", "bold"),
        ("current frame class", "dark blue", "dark cyan"),
        ("focused current frame class", "dark blue", "dark green"),
        ("current frame location", "light cyan", "dark cyan"),
        ("focused current frame location", "light cyan", "dark green"),

        ("breakpoint", "black", "dark cyan"),
        ("focused breakpoint", "black", "dark green"),
        ("current breakpoint", add_setting("white", "bold"), "dark cyan"),
        ("focused current breakpoint", add_setting("white", "bold"), "dark green", "bold"),

        ("selectable", "black", "dark cyan"),
        ("focused selectable", "black", "dark green"),

        ("button", "white", "dark blue"),
        ("focused button", "light cyan", "black"),

        ("background", "black", "light gray"),
        ("hotkey", add_setting("black", "underline"), "light gray", "underline"),
        ("focused sidebar", "yellow", "light gray", "standout"),

        ("warning", add_setting("white", "bold"), "dark red", "standout"),

        ("label", "black", "light gray"),
        ("value", "yellow", "dark blue"),
        ("fixed value", "light gray", "dark blue"),
        ("group head", add_setting("dark blue", "bold"), "light gray"),

        ("search box", "black", "dark cyan"),
        ("search not found", "white", "dark red"),

        ("dialog title", add_setting("white", "bold"), "dark cyan"),

        # highlighting
        ("source", "yellow", "dark blue"),
        ("focused source", "black", "dark green"),
        ("highlighted source", "black", "dark magenta"),
        ("current source", "black", "dark cyan"),
        ("current focused source", "white", "dark cyan"),
        ("current highlighted source", "white", "dark cyan"),

        ("line number", "light gray", "dark blue"),
        ("keyword", add_setting("white", "bold"), "dark blue"),
        ("name", "light cyan", "dark blue"),
        ("literal", "light magenta", "dark blue"),

        ("string", "light magenta", "dark blue"),
        ("doublestring", "light magenta", "dark blue"),
        ("singlestring", "light magenta", "dark blue"),
        ("docstring", "light magenta", "dark blue"),

        ("punctuation", "light gray", "dark blue"),
        ("comment", "light gray", "dark blue"),
        ("bp_star", "dark red", "dark blue"),

        ]

    palette_dict = dict(
            (entry[0], entry[1:]) for entry in palette)

    if theme == "classic":
        pass
    elif theme == "vim":
        palette_dict.update({
            "source": ("black", "default"),
            "keyword": ("brown", "default"),
            "kw_namespace": ("dark magenta", "default"),

            "literal": ("black", "default"),
            "string": ("dark red", "default"),
            "doublestring": ("dark red", "default"),
            "singlestring": ("dark red", "default"),
            "docstring": ("dark red", "default"),

            "punctuation": ("black", "default"),
            "comment": ("dark blue", "default"),
            "classname": ("dark cyan", "default"),
            "name": ("dark cyan", "default"),
            "line number": ("dark gray", "default"),
            "bp_star": ("dark red", "default"),
            })
    elif theme == "dark vim":
        palette_dict.update({
        "header": ("black", "light gray", "standout"),

        # variables view
        "variables": ("black", "dark gray"),
        "variable separator": ("dark cyan", "light gray"),

        "var label": ("light gray", "dark gray"),
        "var value": ("white", "dark gray"),
        "focused var label": ("light gray", "light blue"),
        "focused var value": ("white", "light blue"),

        "highlighted var label": ("light gray", "dark green"),
        "highlighted var value": ("white", "dark green"),
        "focused highlighted var label": ("light gray", "light blue"),
        "focused highlighted var value": ("white", "light blue"),

        "return label": ("light gray", "dark gray"),
        "return value": ("light cyan", "dark gray"),
        "focused return label": ("yellow", "light blue"),
        "focused return value": ("white", "light blue"),

        # stack view
        "stack": ("black", "dark gray"),

        "frame name": ("light gray", "dark gray"),
        "focused frame name": ("light gray", "light blue"),
        "frame class": ("dark blue", "dark gray"),
        "focused frame class": ("dark blue", "light blue"),
        "frame location": ("white", "dark gray"),
        "focused frame location": ("white", "light blue"),

        "current frame name": (add_setting("white", "bold"),
            "dark gray"),
        "focused current frame name": (add_setting("white", "bold"),
            "light blue", "bold"),
        "current frame class": ("dark blue", "dark gray"),
        "focused current frame class": ("dark blue", "dark green"),
        "current frame location": ("light cyan", "dark gray"),
        "focused current frame location": ("light cyan", "light blue"),

        # breakpoint view
        "breakpoint": ("light gray", "dark gray"),
        "focused breakpoint": ("light gray", "light blue"),
        "current breakpoint": (add_setting("white", "bold"), "dark gray"),
        "focused current breakpoint": (add_setting("white", "bold"), "light blue"),

        # UI widgets
        "selectable": ("light gray", "dark gray"),
        "focused selectable": ("white", "light blue"),

        "button": ("light gray", "dark gray"),
        "focused button": ("white", "light blue"),

        "background": ("black", "light gray"),
        "hotkey": (add_setting("black", "underline"), "light gray", "underline"),
        "focused sidebar": ("light blue", "light gray", "standout"),

        "warning": (add_setting("white", "bold"), "dark red", "standout"),

        "label": ("black", "light gray"),
        "value": ("white", "dark gray"),
        "fixed value": ("light gray", "dark gray"),

        "search box": ("white", "dark gray"),
        "search not found": ("white", "dark red"),

        "dialog title": (add_setting("white", "bold"), "dark gray"),

        # source view
        "breakpoint source": ("light gray", "dark red"),
        "breakpoint focused source": ("black", "dark red"),
        "current breakpoint source": ("black", "dark red"),
        "current breakpoint focused source": ("white", "dark red"),

        # highlighting
        "source": ("white", "black"),
        "focused source": ("white", "light blue"),
        "highlighted source": ("black", "dark magenta"),
        "current source": ("black", "light gray"),
        "current focused source": ("white", "dark cyan"),
        "current highlighted source": ("white", "dark cyan"),

        "line number": ("dark gray", "black"),
        "keyword": ("yellow", "black"),

        "literal": ("dark magenta", "black"),
        "string": ("dark magenta", "black"),
        "doublestring": ("dark magenta", "black"),
        "singlestring": ("dark magenta", "black"),
        "docstring": ("dark magenta", "black"),

        "name": ("light cyan", "black"),
        "punctuation": ("yellow", "black"),
        "comment": ("light blue", "black"),
        "bp_star": ("dark red", "black"),
            })
    elif theme == "midnight":
        # Based on XCode's midnight theme
        # Looks best in a console with green text against black background
        palette_dict.update({
            "variables": ("white", "default"),

            "var label": ("light blue", "default"),
            "var value": ("white", "default"),

            "stack": ("white", "default"),

            "frame name": ("white", "default"),
            "frame class": ("dark blue", "default"),
            "frame location": ("light cyan", "default"),

            "current frame name": (add_setting("white", "bold"), "default"),
            "current frame class": ("dark blue", "default"),
            "current frame location": ("light cyan", "default"),

            "breakpoint": ("default", "default"),

            "search box": ("default", "default"),

            "source": ("white", "default"),
            "highlighted source": ("white", "light cyan"),
            "current source": ("white", "light gray"),
            "current focused source": ("white", "brown"),

            "line number": ("light gray", "default"),
            "keyword": ("dark magenta", "default"),
            "name": ("white", "default"),
            "literal": ("dark cyan", "default"),
            "string": ("dark red", "default"),
            "doublestring": ("dark red", "default"),
            "singlestring": ("light blue", "default"),
            "docstring": ("light red", "default"),
            "backtick": ("light green", "default"),
            "punctuation": ("white", "default"),
            "comment": ("dark green", "default"),
            "classname": ("dark cyan", "default"),
            "funcname": ("white", "default"),
            "bp_star": ("dark red", "default"),

        })

    else:
        try:
            symbols = {
                    "palette": palette_dict,
                    "add_setting": add_setting,
                    }

            from os.path import expanduser
            execfile(expanduser(theme), symbols)
        except:
            print "Error when importing theme:"
            from traceback import print_exc
            print_exc()
            raw_input("Hit enter:")

    return [(key,)+value for key, value in palette_dict.iteritems()]

