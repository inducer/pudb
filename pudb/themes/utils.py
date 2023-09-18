import urwid


may_use_fancy_formats = not hasattr(urwid.escape, "_fg_attr_xterm")


def add_setting(color, setting):
    if may_use_fancy_formats:
        return f"{color}, {setting}"
    return color


inheritance_overrides = {}


def link(child: str, parent: str):
    inheritance_overrides[child] = parent


def reset_inheritance_overrides():
    inheritance_overrides.clear()
