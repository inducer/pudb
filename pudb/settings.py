from __future__ import absolute_import, division, print_function

__copyright__ = """
Copyright (C) 2009-2017 Andreas Kloeckner
Copyright (C) 2014-2017 Aaron Meurer
"""

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


import os
import sys

from pudb.py3compat import ConfigParser
from pudb.lowlevel import lookup_module, get_breakpoint_invalid_reason

# minor LGPL violation: stolen from python-xdg

_home = os.environ.get('HOME', None)
xdg_data_home = os.environ.get('XDG_DATA_HOME',
            os.path.join(_home, '.local', 'share') if _home else None)


XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME',
                                 os.path.join(_home, '.config') if _home else None)

if XDG_CONFIG_HOME:
    XDG_CONFIG_DIRS = [XDG_CONFIG_HOME]
else:
    XDG_CONFIG_DIRS = os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg').split(':')


def get_save_config_path(*resource):
    if XDG_CONFIG_HOME is None:
        return None
    if not resource:
        resource = [XDG_CONF_RESOURCE]
    resource = os.path.join(*resource)
    assert not resource.startswith('/')
    path = os.path.join(XDG_CONFIG_HOME, resource)
    if not os.path.isdir(path):
        os.makedirs(path, 448)  # 0o700
    return path

# end LGPL violation


CONF_SECTION = "pudb"
XDG_CONF_RESOURCE = "pudb"
CONF_FILE_NAME = "pudb.cfg"

SAVED_BREAKPOINTS_FILE_NAME = "saved-breakpoints-%d.%d" % sys.version_info[:2]
BREAKPOINTS_FILE_NAME = "breakpoints-%d.%d" % sys.version_info[:2]


def load_config():
    from os.path import join, isdir

    cparser = ConfigParser()

    conf_dict = {}
    try:
        cparser.read([
            join(cdir, XDG_CONF_RESOURCE, CONF_FILE_NAME)
            for cdir in XDG_CONFIG_DIRS if isdir(cdir)])

        if cparser.has_section(CONF_SECTION):
            conf_dict.update(dict(cparser.items(CONF_SECTION)))
    except Exception:
        pass

    conf_dict.setdefault("shell", "internal")
    conf_dict.setdefault("theme", "classic")
    conf_dict.setdefault("line_numbers", False)
    conf_dict.setdefault("seen_welcome", "a")

    conf_dict.setdefault("sidebar_width", 0.5)
    conf_dict.setdefault("variables_weight", 1)
    conf_dict.setdefault("stack_weight", 1)
    conf_dict.setdefault("breakpoints_weight", 1)

    conf_dict.setdefault("current_stack_frame", "top")

    conf_dict.setdefault("stringifier", "type")

    conf_dict.setdefault("custom_theme", "")
    conf_dict.setdefault("custom_stringifier", "")
    conf_dict.setdefault("custom_shell", "")

    conf_dict.setdefault("wrap_variables", True)
    conf_dict.setdefault("default_variables_access_level", "public")

    conf_dict.setdefault("display", "auto")

    conf_dict.setdefault("prompt_on_quit", True)

    conf_dict.setdefault("jk_sidebar_scroll", False)

    def normalize_bool_inplace(name):
        try:
            if conf_dict[name].lower() in ["0", "false", "off"]:
                conf_dict[name] = False
            else:
                conf_dict[name] = True
        except Exception:
            pass

    normalize_bool_inplace("line_numbers")
    normalize_bool_inplace("wrap_variables")
    normalize_bool_inplace("prompt_on_quit")
    normalize_bool_inplace("jk_sidebar_scroll")

    return conf_dict


def save_config(conf_dict):
    from os.path import join

    cparser = ConfigParser()
    cparser.add_section(CONF_SECTION)

    for key in sorted(conf_dict):
        cparser.set(CONF_SECTION, key, str(conf_dict[key]))

    try:
        save_path = get_save_config_path()
        if not save_path:
            return
        outf = open(join(save_path, CONF_FILE_NAME), "w")
        cparser.write(outf)
        outf.close()
    except Exception:
        pass


def edit_config(ui, conf_dict):
    import urwid

    old_conf_dict = conf_dict.copy()

    def _update_theme():
        ui.setup_palette(ui.screen)
        ui.screen.clear()

    def _update_line_numbers():
        for sl in ui.source:
            sl._invalidate()

    def _update_prompt_on_quit():
        pass

    def _update_jk_sidebar_scroll():
        pass

    def _update_current_stack_frame():
        ui.update_stack()

    def _update_stringifier():
        import pudb.var_view
        pudb.var_view.custom_stringifier_dict = {}
        ui.update_var_view()

    def _update_default_variables_access_level():
        ui.update_var_view()

    def _update_wrap_variables():
        ui.update_var_view()

    def _update_config(check_box, new_state, option_newvalue):
        option, newvalue = option_newvalue
        new_conf_dict = {option: newvalue}
        if option == "theme":
            # only activate if the new state of the radio button is 'on'
            if new_state:
                if newvalue is None:
                    # Select the custom theme entry dialog
                    lb.set_focus(lb_contents.index(theme_edit_list_item))
                    return

                conf_dict.update(theme=newvalue)
                _update_theme()

        elif option == "line_numbers":
            new_conf_dict["line_numbers"] = not check_box.get_state()
            conf_dict.update(new_conf_dict)
            _update_line_numbers()

        elif option == "prompt_on_quit":
            new_conf_dict["prompt_on_quit"] = not check_box.get_state()
            conf_dict.update(new_conf_dict)
            _update_prompt_on_quit()

        elif option == "jk_sidebar_scroll":
            new_conf_dict["jk_sidebar_scroll"] = not check_box.get_state()
            conf_dict.update(new_conf_dict)
            _update_jk_sidebar_scroll()

        elif option == "current_stack_frame":
            # only activate if the new state of the radio button is 'on'
            if new_state:
                conf_dict.update(new_conf_dict)
                _update_current_stack_frame()

        elif option == "stringifier":
            # only activate if the new state of the radio button is 'on'
            if new_state:
                if newvalue is None:
                    lb.set_focus(lb_contents.index(stringifier_edit_list_item))
                    return

                conf_dict.update(stringifier=newvalue)
                _update_stringifier()

        elif option == "default_variables_access_level":
            # only activate if the new state of the radio button is 'on'
            if new_state:
                conf_dict.update(default_variables_access_level=newvalue)
                _update_default_variables_access_level()

        elif option == "wrap_variables":
            new_conf_dict["wrap_variables"] = not check_box.get_state()
            conf_dict.update(new_conf_dict)
            _update_wrap_variables()

    heading = urwid.Text("This is the preferences screen for PuDB. "
        "Hit Ctrl-P at any time to get back to it.\n\n"
        "Configuration settings are saved in "
        "$HOME/.config/pudb or $XDG_CONFIG_HOME/pudb "
        "environment variable. If both variables are not set "
        "configurations settings will not be saved.\n")

    cb_line_numbers = urwid.CheckBox("Show Line Numbers",
            bool(conf_dict["line_numbers"]), on_state_change=_update_config,
                user_data=("line_numbers", None))

    cb_prompt_on_quit = urwid.CheckBox("Prompt before quitting",
            bool(conf_dict["prompt_on_quit"]), on_state_change=_update_config,
                user_data=("prompt_on_quit", None))

    cb_jk_sidebar_scroll = urwid.CheckBox("Use j/k keys for scrolling in "
                                          "sidebar",
            bool(conf_dict["jk_sidebar_scroll"]), on_state_change=_update_config,
                user_data=("jk_sidebar_scroll", None))

    # {{{ shells

    shell_info = urwid.Text("This is the shell that will be "
            "used when you hit '!'.\n")
    shells = ["internal", "classic", "ipython", "bpython", "ptpython", "ptipython"]
    known_shell = conf_dict["shell"] in shells
    shell_edit = urwid.Edit(edit_text=conf_dict["custom_shell"])
    shell_edit_list_item = urwid.AttrMap(shell_edit, "value")

    shell_rb_group = []
    shell_rbs = [
            urwid.RadioButton(shell_rb_group, name,
                conf_dict["shell"] == name)
            for name in shells]+[
                urwid.RadioButton(shell_rb_group, "Custom:",
                not known_shell, on_state_change=_update_config,
                user_data=("shell", None)),
                shell_edit_list_item,
                urwid.Text("\nTo use a custom shell, see example-shell.py "
                    "in the pudb distribution. Enter the full path to a "
                    "file like it in the box above. '~' will be expanded "
                    "to your home directory. The file should contain a "
                    "function called pudb_shell(_globals, _locals) "
                    "at the module level. See the PuDB documentation for "
                    "more information."),
            ]

    # }}}

    # {{{ themes

    from pudb.theme import THEMES

    known_theme = conf_dict["theme"] in THEMES

    theme_rb_group = []
    theme_edit = urwid.Edit(edit_text=conf_dict["custom_theme"])
    theme_edit_list_item = urwid.AttrMap(theme_edit, "value")
    theme_rbs = [
            urwid.RadioButton(theme_rb_group, name,
                conf_dict["theme"] == name, on_state_change=_update_config,
                user_data=("theme", name))
            for name in THEMES]+[
                urwid.RadioButton(theme_rb_group, "Custom:",
                    not known_theme, on_state_change=_update_config,
                    user_data=("theme", None)),
                theme_edit_list_item,
                urwid.Text("\nTo use a custom theme, see example-theme.py in the "
                    "pudb distribution. Enter the full path to a file like it in "
                    "the box above. '~' will be expanded to your home directory. "
                    "Note that a custom theme will not be applied until you close "
                    "this dialog."),
            ]

    # }}}

    # {{{ stack

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

    # }}}

    # {{{ stringifier

    stringifier_opts = ["type", "str", "repr"]
    known_stringifier = conf_dict["stringifier"] in stringifier_opts
    stringifier_rb_group = []
    stringifier_edit = urwid.Edit(edit_text=conf_dict["custom_stringifier"])
    stringifier_info = urwid.Text("This is the default function that will be "
        "called on variables in the variables list.  Note that you can change "
        "this on a per-variable basis by selecting a variable and hitting Enter "
        "or by typing t/s/r.  Note that str and repr will be slower than type "
        "and have the potential to crash PuDB.\n")
    stringifier_edit_list_item = urwid.AttrMap(stringifier_edit, "value")
    stringifier_rbs = [
            urwid.RadioButton(stringifier_rb_group, name,
                conf_dict["stringifier"] == name,
                on_state_change=_update_config,
                user_data=("stringifier", name))
            for name in stringifier_opts
            ]+[
                urwid.RadioButton(stringifier_rb_group, "Custom:",
                    not known_stringifier, on_state_change=_update_config,
                    user_data=("stringifier", None)),
                stringifier_edit_list_item,
                urwid.Text("\nTo use a custom stringifier, see "
                    "example-stringifier.py in the pudb distribution. Enter the "
                    "full path to a file like it in the box above. "
                    "'~' will be expanded to your home directory. "
                    "The file should contain a function called pudb_stringifier() "
                    "at the module level, which should take a single argument and "
                    "return the desired string form of the object passed to it. "
                    "Note that if you choose a custom stringifier, the variables "
                    "view will not be updated until you close this dialog."),
            ]

    # }}}

    # {{{ variables access level

    default_variables_access_level_opts = ["public", "private", "all"]
    default_variables_access_level_rb_group = []
    default_variables_access_level_info = urwid.Text(
            "Set the default attribute visibility "
            "of variables in the variables list.\n"
            "\nNote that you can change this option on "
            "a per-variable basis by selecting the "
            "variable and pressing '*'.")
    default_variables_access_level_rbs = [
            urwid.RadioButton(default_variables_access_level_rb_group, name,
                conf_dict["default_variables_access_level"] == name,
                on_state_change=_update_config,
                user_data=("default_variables_access_level", name))
            for name in default_variables_access_level_opts
            ]

    # }}}

    # {{{ wrap variables

    cb_wrap_variables = urwid.CheckBox("Wrap variables",
            bool(conf_dict["wrap_variables"]), on_state_change=_update_config,
                user_data=("wrap_variables", None))

    wrap_variables_info = urwid.Text("\nNote that you can change this option on "
                                     "a per-variable basis by selecting the "
                                     "variable and pressing 'w'.")

    # }}}

    # {{{ display

    display_info = urwid.Text("What driver is used to talk to your terminal. "
            "'raw' has the most features (colors and highlighting), "
            "but is only correct for "
            "XTerm and terminals like it. 'curses' "
            "has fewer "
            "features, but it will work with just about any terminal. 'auto' "
            "will attempt to pick between the two based on availability and "
            "the $TERM environment variable.\n\n"
            "Changing this setting requires a restart of PuDB.")

    displays = ["auto", "raw", "curses"]

    display_rb_group = []
    display_rbs = [
            urwid.RadioButton(display_rb_group, name,
                conf_dict["display"] == name)
            for name in displays]

    # }}}

    lb_contents = (
            [heading]
            + [urwid.AttrMap(urwid.Text("Line Numbers:\n"), "group head")]
            + [cb_line_numbers]

            + [urwid.AttrMap(urwid.Text("\nPrompt on quit:\n"), "group head")]
            + [cb_prompt_on_quit]

            + [urwid.AttrMap(urwid.Text("\nKeys:\n"), "group head")]
            + [cb_jk_sidebar_scroll]

            + [urwid.AttrMap(urwid.Text("\nShell:\n"), "group head")]
            + [shell_info]
            + shell_rbs

            + [urwid.AttrMap(urwid.Text("\nTheme:\n"), "group head")]
            + theme_rbs

            + [urwid.AttrMap(urwid.Text("\nStack Order:\n"), "group head")]
            + [stack_info]
            + stack_rbs

            + [urwid.AttrMap(urwid.Text("\nVariable Stringifier:\n"), "group head")]
            + [stringifier_info]
            + stringifier_rbs

            + [urwid.AttrMap(urwid.Text("\nVariables Attribute Visibility:\n"),
                "group head")]
            + [default_variables_access_level_info]
            + default_variables_access_level_rbs

            + [urwid.AttrMap(urwid.Text("\nWrap Variables:\n"), "group head")]
            + [cb_wrap_variables]
            + [wrap_variables_info]

            + [urwid.AttrMap(urwid.Text("\nDisplay driver:\n"), "group head")]
            + [display_info]
            + display_rbs
            )

    lb = urwid.ListBox(urwid.SimpleListWalker(lb_contents))

    if ui.dialog(lb,         [
            ("OK", True),
            ("Cancel", False),
            ],
            title="Edit Preferences"):
        # Only update the settings here that instant-apply (above) doesn't take
        # care of.

        # if we had a custom theme, it wasn't updated live
        if theme_rb_group[-1].state:
            newvalue = theme_edit.get_edit_text()
            conf_dict.update(theme=newvalue, custom_theme=newvalue)
            _update_theme()

        # Ditto for custom stringifiers
        if stringifier_rb_group[-1].state:
            newvalue = stringifier_edit.get_edit_text()
            conf_dict.update(stringifier=newvalue, custom_stringifier=newvalue)
            _update_stringifier()

        if shell_rb_group[-1].state:
            newvalue = shell_edit.get_edit_text()
            conf_dict.update(shell=newvalue, custom_shell=newvalue)
        else:
            for shell, shell_rb in zip(shells, shell_rbs):
                if shell_rb.get_state():
                    conf_dict["shell"] = shell

        for display, display_rb in zip(displays, display_rbs):
            if display_rb.get_state():
                conf_dict["display"] = display

    else:  # The user chose cancel, revert changes
        conf_dict.update(old_conf_dict)
        _update_theme()
        # _update_line_numbers() is equivalent to _update_theme()
        _update_current_stack_frame()
        _update_stringifier()


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

            f = lookup_module(filename)
            if not f:
                continue
            else:
                filename = f

            arg = arg[colon+1:].lstrip()
            try:
                lineno = int(arg)
            except ValueError:
                continue
        else:
            continue

        if get_breakpoint_invalid_reason(filename, lineno) is None:
            breakpoints.append((filename, lineno, False, cond, funcname))

    return breakpoints


def get_breakpoints_file_name():
    from os.path import join
    save_path = get_save_config_path()
    if not save_path:
        return None
    else:
        return join(save_path, SAVED_BREAKPOINTS_FILE_NAME)


def load_breakpoints():
    """
    Loads and check saved breakpoints out from files
    Returns: list of tuples
    """
    from os.path import join, isdir

    file_names = []
    for cdir in XDG_CONFIG_DIRS:
        if isdir(cdir):
            for name in [SAVED_BREAKPOINTS_FILE_NAME, BREAKPOINTS_FILE_NAME]:
                file_names.append(join(cdir, XDG_CONF_RESOURCE, name))

    lines = []
    for fname in file_names:
        try:
            rc_file = open(fname, "rt")
        except IOError:
            pass
        else:
            lines.extend([l.strip() for l in rc_file.readlines()])
            rc_file.close()

    return parse_breakpoints(lines)


def save_breakpoints(bp_list):
    """
    :arg bp_list: a list of `bdb.Breakpoint` objects
    """
    save_path = get_breakpoints_file_name()
    if not save_path:
        return

    histfile = open(get_breakpoints_file_name(), 'w')
    bp_list = set([(bp.file, bp.line, bp.cond) for bp in bp_list])
    for bp in bp_list:
        line = "b %s:%d" % (bp[0], bp[1])
        if bp[2]:
            line += ", %s" % bp[2]
        line += "\n"
        histfile.write(line)
    histfile.close()

# }}}

# vim:foldmethod=marker
