def get_palette(may_use_fancy_formats):
    if may_use_fancy_formats:
        def add_setting(color, setting):
            return color+","+setting
    else:
        def add_setting(color, setting):
            return color

    return [
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

        ("keyword", add_setting("white", "bold"), "dark blue"),
        ("literal", "light magenta", "dark blue"),
        ("punctuation", "light gray", "dark blue"),
        ("comment", "light gray", "dark blue"),

        ]

