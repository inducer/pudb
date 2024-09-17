from pudb.themes.utils import add_setting, link


# ------------------------------------------------------------------------------
# Colors are approximations of https://www.nordtheme.com/docs/colors-and-palettes
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Polar Night is made up of four darker colors (nord 0, nord1, nord2, and nord3)
# that are commonly used for base elements like backgrounds or text color in
# bright ambiance designs.
# ------------------------------------------------------------------------------

# nord0 is the origin color or the Polar Night palette.
nord0 = "h236"

# nord1 is a brighter shade color based on nord0.
nord1 = "h238"

# nord2 is an even more brighter shade color of nord0.
nord2 = "h239"

# nord3 is the brightest shade color based on nord0.
nord3 = "h243"

# ------------------------------------------------------------------------------
# Snow Storm is made up of three bright colors that are commonly used for text
# colors or base UI elements in bright ambiance designs.
# ------------------------------------------------------------------------------

# nord4 is the origin color or the Snow Storm palette.
nord4 = "h253"

# nord5 is a brighter shade color of nord4.
nord5 = "h254"

# nord6 is the brightest shade color based on nord4.
nord6 = "h255"

# ------------------------------------------------------------------------------
# Frost can be described as the heart palette of Nord, a group of four bluish
# colors that are commonly used for primary UI component and text highlighting
# and essential code syntax elements.
# ------------------------------------------------------------------------------

# nord7 is a calm and highly contrasted color reminiscent of
# frozen polar water.
nord7 = "h109"

# nord8 is a bright and shiny primary accent color reminiscent of pure
# and clear ice.
nord8 = "h110"

# nord9 is a more darkened and less saturated color reminiscent of
# arctic waters.
nord9 = "h111"

# nord10 is a dark and intensive color reminiscent of the deep arctic ocean.
nord10 = "h67"

# ------------------------------------------------------------------------------
# Aurora consists of five colorful components reminiscent of the "Aurora
# borealis", sometimes referred to as polar lights or northern lights.
# ------------------------------------------------------------------------------

# nord11 is a reddish color.
nord11 = "h138"

# nord12 is an orangey color.
nord12 = "h174"

# nord13 is a yellowy color.
nord13 = "h216"

# nord14 is a greenish color.
nord14 = "h150"

# nord15 is a purplish color.
nord15 = "h139"

link("current breakpoint", "current frame name")
link("focused current breakpoint", "focused current frame name")
palette_dict = {

    # {{{ base styles
    "background": (nord0, nord7),
    "selectable": (nord4, nord1),
    "focused selectable": (nord4, nord2),
    "highlighted": (nord14, nord1),
    "hotkey": (add_setting(nord0, "underline"), nord7),
    # }}}
    # {{{ general ui
    "input": (nord4, nord0),
    "button": (add_setting(nord4, "bold"), nord0),
    "focused button": (add_setting(nord4, "bold"), nord2),
    "focused sidebar": (nord0, nord7),
    "warning": (nord12, nord2),
    "group head": (add_setting(nord0, "bold"), nord7),
    "dialog title": (add_setting(nord4, "bold"), nord1),
    # }}}
    # {{{ source view
    "source": (nord4, nord0),
    "current source": (nord13, nord1),
    "current focused source": (nord13, nord2),
    "breakpoint source": (nord12, nord0),
    "line number": (nord2, nord0),
    "current line marker": (add_setting(nord13, "bold"), nord0),
    "breakpoint marker": (add_setting(nord13, "bold"), nord0),
    # }}}
    # {{{ sidebar
    "sidebar two": (nord7, nord1),
    "focused sidebar two": (nord7, nord2),
    "sidebar three": (nord10, nord1),
    "focused sidebar three": (nord10, nord2),
    # }}}
    # {{{ variables view
    "highlighted var label": (nord14, nord1),
    "focused highlighted var label": (nord14, nord2),
    "focused highlighted var value": (nord14, nord2),
    "return label": (nord0, nord8),
    "focused return label": (nord0, nord8),
    # }}}
    # {{{ stack
    "current frame name": (nord14, nord1),
    "focused current frame name": (nord14, nord2),
    # }}}
    # {{{ shell
    "command line prompt": (add_setting(nord5, "bold"), nord0),
    "command line output": (nord7, nord0),
    "command line error": (nord12, nord0),
    "focused command line output": (nord7, nord2),
    "focused command line error": (nord12, nord2),
    # }}}
    # {{{ Code syntax
    "literal":     (nord15, nord0),
    "builtin":     (add_setting(nord7, "bold"), nord0),
    "pseudo":      (nord7, nord0),
    "exception":   (nord11, nord0),
    "function":    (nord7, nord0),
    "class":       (add_setting(nord9, "underline"), nord0),
    "keyword":     (nord8, nord0),
    "keyword2":    (nord9, nord0),
    "operator":    (nord8, nord0),
    "comment":     (nord3, nord0),
    "string":      (nord14, nord0),
    # }}}
}

# vim: foldmethod=marker
