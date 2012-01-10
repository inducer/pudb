try:
    import IPython
except ImportError:
    HAVE_IPYTHON = False
else:
    HAVE_IPYTHON = True


# readline wrangling ----------------------------------------------------------
def setup_readline():
    import os
    import atexit

    from pudb.settings import get_save_config_path
    histfile = os.path.join(
            get_save_config_path(),
            "shell-history")

    if os.access(histfile, os.R_OK):
        readline.read_history_file(histfile)
    atexit.register(readline.write_history_file, histfile)
    readline.parse_and_bind("tab: complete")


try:
    import readline
    import rlcompleter
    HAVE_READLINE = True
except ImportError:
    HAVE_READLINE = False
else:
    setup_readline()


# combined locals/globals dict ------------------------------------------------
class SetPropagatingDict(dict):
    def __init__(self, source_dicts, target_dict):
        dict.__init__(self)
        for s in source_dicts:
            self.update(s)

        self.target_dict = target_dict

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.target_dict[key] = value

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        del self.target_dict[key]


def run_classic_shell(locals, globals, first_time):
    if first_time:
        banner = "Hit Ctrl-D to return to PuDB."
    else:
        banner = ""

    ns = SetPropagatingDict([locals, globals], locals)

    if HAVE_READLINE:
        readline.set_completer(
                rlcompleter.Completer(ns).complete)

    from code import InteractiveConsole
    cons = InteractiveConsole(ns)

    cons.interact(banner)


def run_ipython_shell_v10(locals, globals, first_time):
    '''IPython shell from IPython version 0.10'''
    if first_time:
        banner = "Hit Ctrl-D to return to PuDB."
    else:
        banner = ""

    # avoid IPython's namespace litter
    ns = locals.copy()

    from IPython.Shell import IPShell
    IPShell(argv=[], user_ns=ns, user_global_ns=globals) \
            .mainloop(banner=banner)

def run_ipython_shell_v11(locals, globals, first_time):
    '''IPython shell from IPython version 0.11'''
    if first_time:
        banner = "Hit Ctrl-D to return to PuDB."
    else:
        banner = ""

    from IPython.frontend.terminal.interactiveshell import \
            TerminalInteractiveShell
    from IPython.frontend.terminal.ipapp import load_default_config
    # XXX: in the future it could be useful to load a 'pudb' config for the
    # user (if it exists) that could contain the user's macros and other
    # niceities.
    config = load_default_config()
    shell = TerminalInteractiveShell.instance(config=config,
            banner2=banner)
    # XXX This avoids a warning about not having unique session/line numbers.
    # See the HistoryManager.writeout_cache method in IPython.core.history.
    shell.history_manager.new_session()
    # Save the originating namespace
    old_locals = shell.user_ns
    old_globals = shell.user_global_ns
    # Update shell with current namespace
    _update_ns(shell, locals, globals)
    shell.mainloop(banner)
    # Restore originating namespace
    _update_ns(shell, old_locals, old_globals)

def _update_ns(shell, locals, globals):
    '''Update the IPython 0.11 namespace at every visit'''

    shell.user_ns = locals.copy()

    try:
        shell.user_global_ns = globals
    except AttributeError:
        class DummyMod(object):
            "A dummy module used for IPython's interactive namespace."
            pass

        user_module = DummyMod()
        user_module.__dict__ = globals
        shell.user_module = user_module

    shell.init_user_ns()
    shell.init_completer()

# Set the proper ipython shell
if HAVE_IPYTHON and hasattr(IPython, 'Shell'):
    run_ipython_shell = run_ipython_shell_v10
else:
    run_ipython_shell = run_ipython_shell_v11

