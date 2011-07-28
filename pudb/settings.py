import os
from ConfigParser import ConfigParser

# minor LGPL violation: stolen from python-xdg

_home = os.environ.get('HOME', '/')
xdg_data_home = os.environ.get('XDG_DATA_HOME',
            os.path.join(_home, '.local', 'share'))

xdg_config_home = os.environ.get('XDG_CONFIG_HOME',
            os.path.join(_home, '.config'))

xdg_config_dirs = [xdg_config_home] + \
    os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg').split(':')

def get_save_config_path(*resource):
    if not resource:
        resource = [XDG_CONF_RESOURCE]
    resource = os.path.join(*resource)
    assert not resource.startswith('/')
    path = os.path.join(xdg_config_home, resource)
    if not os.path.isdir(path):
        os.makedirs(path, 0700)
    return path

# end LGPL violation

CONF_SECTION = "pudb"
XDG_CONF_RESOURCE = "pudb"
CONF_FILE_NAME = "pudb.cfg"
SAVED_BREAKPOINTS_FILE_NAME = "saved-breakpoints"
BREAKPOINTS_FILE_NAME = "breakpoints"




def load_config():
    from os.path import join, isdir

    cparser = ConfigParser()

    conf_dict = {}
    try:
        cparser.read([
            join(cdir, XDG_CONF_RESOURCE, CONF_FILE_NAME)
            for cdir in xdg_config_dirs if isdir(cdir)])

        if cparser.has_section(CONF_SECTION):
            conf_dict.update(dict(cparser.items(CONF_SECTION)))
    except:
        pass

    conf_dict.setdefault("shell", "classic")
    conf_dict.setdefault("theme", "classic")
    conf_dict.setdefault("line_numbers", False)
    conf_dict.setdefault("seen_welcome", "a")

    conf_dict.setdefault("sidebar_width", 0.5)
    conf_dict.setdefault("variables_weight", 1)
    conf_dict.setdefault("stack_weight", 1)
    conf_dict.setdefault("breakpoints_weight", 1)

    conf_dict.setdefault("current_stack_frame", "top")

    def normalize_bool_inplace(name):
        try:
            if conf_dict[name].lower() in ["0", "false", "off"]:
                conf_dict[name] = False
        except:
            pass

    normalize_bool_inplace("line_numbers")

    return conf_dict




def save_config(conf_dict):
    from os.path import join

    cparser = ConfigParser()
    cparser.add_section(CONF_SECTION)

    for key, val in conf_dict.iteritems():
        cparser.set(CONF_SECTION, key, val)

    try:
        outf = open(join(get_save_config_path(),
            CONF_FILE_NAME), "w")
        cparser.write(outf)
        outf.close()
    except:
        pass




def edit_config(ui, conf_dict):
    import urwid

    old_conf_dict = conf_dict.copy()

    def _update_theme():
        ui.setup_palette(ui.screen)

        for sl in ui.source:
            sl._invalidate()

    def _update_line_numbers():
        for sl in ui.source:
                sl._invalidate()

    def _update_current_stack_frame():
        ui.update_stack()

    def _update_config(check_box, new_state, option_newvalue):
        option, newvalue = option_newvalue
        new_conf_dict = {option: newvalue}
        if option == "theme":
            # only activate if the new state of the radio button is 'on'
            if new_state:
                if newvalue is None:
                    newvalue = theme_edit.get_edit_text()

                conf_dict.update(theme=newvalue)
                _update_theme()

        elif option == "line_numbers":
            new_conf_dict["line_numbers"] = not check_box.get_state()
            conf_dict.update(new_conf_dict)
            _update_line_numbers()

        elif option == "current_stack_frame":
            # only activate if the new state of the radio button is 'on'
            if new_state:
                conf_dict.update(new_conf_dict)
                _update_current_stack_frame()
    heading = urwid.Text("This is the preferences screen for PuDB. "
        "Hit Ctrl-P at any time to get back to it.\n\n"
        "Configuration settings are saved in "
        "%s.\n" % get_save_config_path())

    cb_line_numbers = urwid.CheckBox("Show Line Numbers",
            bool(conf_dict["line_numbers"]), on_state_change=_update_config,
                user_data=("line_numbers", None))

    shell_info = urwid.Text("This is the shell that will be used when you hit '!'.\n")
    shells = ["classic", "ipython"]

    shell_rb_grp = []
    shell_rbs = [
            urwid.RadioButton(shell_rb_grp, name,
                conf_dict["shell"] == name)
            for name in shells]

    from pudb.theme import THEMES

    known_theme = conf_dict["theme"] in THEMES

    theme_rb_grp = []
    theme_edit = urwid.Edit(edit_text=conf_dict["theme"])
    theme_rbs = [
            urwid.RadioButton(theme_rb_grp, name,
                conf_dict["theme"] == name, on_state_change=_update_config,
                user_data=("theme", name))
            for name in THEMES]+[
            urwid.RadioButton(theme_rb_grp, "Custom:",
                not known_theme, on_state_change=_update_config,
                user_data=("theme", None)),
            urwid.Padding(
                urwid.AttrMap(theme_edit, "value"),
                left=4),

            urwid.Text("\nTo use a custom theme, see example-theme.py in the "
                "pudb distribution. Enter the full path to a file like it in the "
                "box above. '~' will be expanded to your home directory."),
            ]

    stack_rb_group = []
    stack_opts = ["top", "bottom"]
    stack_info = urwid.Text("Show the current stack frame at the\n")
    stack_rbs = [
            urwid.RadioButton(stack_rb_group, name,
                conf_dict["current_stack_frame"] == name,
                on_state_change=_update_config,
                user_data=("current_stack_frame", name))
            for name in stack_opts
            ]

    if ui.dialog(
            urwid.ListBox(
                [heading]
                + [cb_line_numbers]
                + [urwid.Text("")]
                + [urwid.AttrMap(urwid.Text("Shell:\n"), "group head")]
                + [shell_info]
                + shell_rbs
                + [urwid.AttrMap(urwid.Text("\nTheme:\n"), "group head")]
                + theme_rbs
                + [urwid.AttrMap(urwid.Text("\nStack Order:\n"), "group head")]
                + [stack_info]
                + stack_rbs
                ),
            [
                ("OK", True),
                ("Cancel", False),
                ],
            title="Edit Preferences"):

        # Only update the shell setting here. Instant-apply (above) takes care
        # of updating everything else.

        for shell, shell_rb in zip(shells, shell_rbs):
            if shell_rb.get_state():
                conf_dict["shell"] = shell

    else: # The user chose cancel, revert changes
        conf_dict.update(old_conf_dict)
        _update_theme()
        # _update_line_numbers() is equivalent to _update_theme()
        _update_current_stack_frame()



# {{{ breakpoint saving

def parse_breakpoints(lines):
    # b [ (filename:lineno | function) [, "condition"] ]

    breakpoints = []
    for arg in lines:
        if not arg:
            continue
        arg = arg[1:]

        filename = None
        lineno = None
        cond = None
        comma = arg.find(',')

        if comma > 0:
            # parse stuff after comma: "condition"
            cond = arg[comma+1:].lstrip()
            arg = arg[:comma].rstrip()

        colon = arg.rfind(':')
        funcname = None

        if colon > 0:
            filename = arg[:colon].strip()

            from pudb.lowlevel import lookup_module
            f = lookup_module(filename)

            if not f:
                continue
            else:
                filename = f

            arg = arg[colon+1:].lstrip()
            try:
                lineno = int(arg)
            except ValueError, msg:
                continue
        else:
            continue

        from pudb.lowlevel import get_breakpoint_invalid_reason
        if get_breakpoint_invalid_reason(filename, lineno) is None:
            breakpoints.append((filename, lineno, False, cond, funcname))

    return breakpoints




def load_breakpoints(dbg):
    from os.path import join, isdir

    file_names = [
            join(cdir, XDG_CONF_RESOURCE, name)
            for cdir in xdg_config_dirs if isdir(cdir)
            for name in [SAVED_BREAKPOINTS_FILE_NAME, BREAKPOINTS_FILE_NAME]
            ]

    lines = []
    for fname in file_names:
        try:
            rcFile = open(fname)
        except IOError:
            pass
        else:
            lines.extend([l.strip() for l in rcFile.readlines()])
            rcFile.close()

    return parse_breakpoints(lines)





def save_breakpoints(bp_list):
    """
    :arg bp_list: a list of tuples `(file_name, line)`
    """

    from os.path import join
    bp_histfile = join(get_save_config_path(), "saved-breakpoints")
    histfile = open(bp_histfile, 'w')
    for bp in bp_list:
        histfile.write("b %s:%d\n"%(bp.file, bp.line))
    histfile.close()

# }}}

# vim:foldmethod=marker
