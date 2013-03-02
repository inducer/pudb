# Supported 16 color values:
#   'h0' (color number 0) through 'h15' (color number 15)
#    or
#   'default' (use the terminal's default foreground),
#   'black', 'dark red', 'dark green', 'brown', 'dark blue',
#   'dark magenta', 'dark cyan', 'light gray', 'dark gray',
#   'light red', 'light green', 'yellow', 'light blue', 
#   'light magenta', 'light cyan', 'white'
#
# Supported 256 color values:
#   'h0' (color number 0) through 'h255' (color number 255)
#
# 256 color chart: http://en.wikipedia.org/wiki/File:Xterm_color_chart.png
#
# "setting_name": (foreground_color, background_color),

palette.update({
    "source": (add_setting("black", "underline"), "dark green"),
    "comment": ("h250", "default")
    })
