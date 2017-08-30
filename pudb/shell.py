from __future__ import absolute_import, division, print_function

try:
    import bpython  # noqa
    # Access a property to verify module exists in case
    # there's a demand loader wrapping module imports
    # See https://github.com/inducer/pudb/issues/177
    bpython.__version__
except ImportError:
    HAVE_BPYTHON = False
else:
    HAVE_BPYTHON = True

try:
    from ptpython.ipython import embed as ptipython_embed
except ImportError:
    HAVE_PTIPYTHON = False
else:
    HAVE_PTIPYTHON = True

try:
    from ptpython.repl import embed as ptpython_embed, run_config
except ImportError:
    HAVE_PTPYTHON = False
else:
    HAVE_PTPYTHON = True


try:
    import readline
    import rlcompleter
    HAVE_READLINE = True
except ImportError:
    HAVE_READLINE = False


# {{{ combined locals/globals dict

class SetPropagatingDict(dict):
    """
    Combine dict into one, with assignments affecting a target dict

    The source dicts are combined so that early dicts in the list have higher
    precedence.

    Typical usage is ``SetPropagatingDict([locals, globals], locals)``. This
    is used for functions like ``rlcompleter.Completer`` and
    ``code.InteractiveConsole``, which only take a single dictionary. This
    way, changes made to it are propagated to locals. Note that assigning to
    locals only actually works at the module level, when ``locals()`` is the
    same as ``globals()``, so propagation doesn't happen at all if the
    debugger is inside a function frame.

    """
    def __init__(self, source_dicts, target_dict):
        dict.__init__(self)
        for s in source_dicts[::-1]:
            self.update(s)

        self.target_dict = target_dict

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.target_dict[key] = value

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        del self.target_dict[key]

# }}}


custom_shell_dict = {}


def run_classic_shell(globals, locals, first_time=[True]):
    if first_time:
        banner = "Hit Ctrl-D to return to PuDB."
        first_time.pop()
    else:
        banner = ""

    ns = SetPropagatingDict([locals, globals], locals)

    from pudb.settings import get_save_config_path
    from os.path import join
    hist_file = join(
            get_save_config_path(),
            "shell-history")

    if HAVE_READLINE:
        readline.set_completer(
                rlcompleter.Completer(ns).complete)
        readline.parse_and_bind("tab: complete")
        readline.clear_history()
        try:
            readline.read_history_file(hist_file)
        except IOError:
            pass

    from code import InteractiveConsole
    cons = InteractiveConsole(ns)

    cons.interact(banner)

    if HAVE_READLINE:
        readline.write_history_file(hist_file)


def run_bpython_shell(globals, locals):
    ns = SetPropagatingDict([locals, globals], locals)

    import bpython.cli
    bpython.cli.main(args=[], locals_=ns)


# {{{ ipython

def have_ipython():
    # IPython has started being obnoxious on import, only import
    # if absolutely needed.

    # https://github.com/ipython/ipython/issues/9435

    try:
        import IPython
        # Access a property to verify module exists in case
        # there's a demand loader wrapping module imports
        # See https://github.com/inducer/pudb/issues/177
        IPython.core
    except (ImportError, ValueError):
        # Old IPythons versions (0.12?) may fail to import with
        # ValueError: fallback required, but not specified
        # https://github.com/inducer/pudb/pull/135
        return False
    else:
        return True


def ipython_version():
    if have_ipython():
        from IPython import version_info
        return version_info
    else:
        return None


def run_ipython_shell_v10(globals, locals, first_time=[True]):
    '''IPython shell from IPython version 0.10'''
    if first_time:
        banner = "Hit Ctrl-D to return to PuDB."
        first_time.pop()
    else:
        banner = ""

    # avoid IPython's namespace litter
    ns = locals.copy()

    from IPython.Shell import IPShell
    IPShell(argv=[], user_ns=ns, user_global_ns=globals) \
            .mainloop(banner=banner)


def _update_ipython_ns(shell, globals, locals):
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


def run_ipython_shell_v11(globals, locals, first_time=[True]):
    '''IPython shell from IPython version 0.11'''
    if first_time:
        banner = "Hit Ctrl-D to return to PuDB."
        first_time.pop()
    else:
        banner = ""

    try:
        # IPython 1.0 got rid of the frontend intermediary, and complains with
        # a deprecated warning when you use it.
        from IPython.terminal.interactiveshell import TerminalInteractiveShell
        from IPython.terminal.ipapp import load_default_config
    except ImportError:
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
    _update_ipython_ns(shell, globals, locals)

    args = []
    if ipython_version() < (5, 0, 0):
        args.append(banner)
    else:
        print(banner)
    shell.mainloop(*args)

    # Restore originating namespace
    _update_ipython_ns(shell, old_globals, old_locals)


def run_ipython_shell(globals, locals):
    import IPython
    if have_ipython() and hasattr(IPython, 'Shell'):
        return run_ipython_shell_v10(globals, locals)
    else:
        return run_ipython_shell_v11(globals, locals)

# }}}


def run_ptpython_shell(globals, locals):
    # Use the default ptpython history
    import os
    history_filename = os.path.expanduser('~/.ptpython/history')
    ptpython_embed(globals=globals.copy(), locals=locals.copy(),
                   history_filename=history_filename,
                   configure=run_config)


def run_ptipython_shell(globals, locals):
    # Use the default ptpython history
    import os

    history_filename = os.path.expanduser('~/.ptpython/history')
    ptipython_embed(globals=globals.copy(), locals=locals.copy(),
                   history_filename=history_filename,
                   configure=run_config)

# vim: foldmethod=marker
