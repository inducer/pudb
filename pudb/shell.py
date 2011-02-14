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

    histfile = os.path.join(os.environ["HOME"], ".pudb-history")
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




def run_ipython_shell(locals, globals, first_time):
    if first_time:
        banner = "Hit Ctrl-D to return to PuDB."
    else:
        banner = ""

    # avoid IPython's namespace litter
    ns = locals.copy()

    from IPython.Shell import IPShell
    IPShell(argv=[], user_ns=ns, user_global_ns=globals) \
            .mainloop(banner=banner)
