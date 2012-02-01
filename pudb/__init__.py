NUM_VERSION = (2012, 1)
VERSION = ".".join(str(nv) for nv in NUM_VERSION)




from pudb.settings import load_config, save_config
CONFIG = load_config()
save_config(CONFIG)




CURRENT_DEBUGGER = []
def _get_debugger():
    if not CURRENT_DEBUGGER:
        from pudb.debugger import Debugger
        dbg = Debugger()
        CURRENT_DEBUGGER.append(dbg)
        return dbg
    else:
        return CURRENT_DEBUGGER[0]




def runscript(mainpyfile, args=None, pre_run="", steal_output=False):
    from pudb.debugger import Debugger
    dbg = Debugger(steal_output=steal_output)

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user from the command line. The best approach would be to
    # have a "restart" command which would allow explicit specification of
    # command line arguments.

    import sys
    if args is not None:
        prev_sys_argv = sys.argv[:]
        sys.argv = [mainpyfile] + args

    # replace pudb's dir with script's dir in front of module search path.
    from os.path import dirname
    prev_sys_path = sys.path[:]
    sys.path[0] = dirname(mainpyfile)

    from pudb.settings import load_breakpoints
    for bpoint_descr in load_breakpoints(dbg):
        dbg.set_break(*bpoint_descr)

    while True:
        if pre_run:
            from subprocess import call
            retcode = call(pre_run, close_fds=True, shell=True)
            if retcode:
                print "*** WARNING: pre-run process exited with code %d." % retcode
                raw_input("[Hit Enter]")

        status_msg = ""

        try:
            dbg._runscript(mainpyfile)
        except SystemExit, se:
            status_msg = "The debuggee exited normally with status code %s.\n\n" % se.code
        except:
            dbg.post_mortem = True
            dbg.interaction(None, sys.exc_info())

        def quit_debugger(w, size, key):
            dbg.ui.quit_event_loop = ["quit"]

        import urwid
        pre_run_edit = urwid.Edit("", pre_run)

        result = dbg.ui.call_with_ui(dbg.ui.dialog,
            urwid.ListBox([urwid.Text(
                "Your PuDB session has ended.\n\n%s"
                "Would you like to quit PuDB or restart your program?\n"
                "You may hit 'q' to quit."
                % status_msg),
                urwid.Text("\n\nIf you decide to restart, this command will be run prior to "
                "actually restarting:"),
                urwid.AttrMap(pre_run_edit, "value")
                ]),
            [
                ("Restart", "restart"),
                ("Quit", "quit"),
                ],
            focus_buttons=True,
            bind_enter_esc=False,
            title="Finished",
            extra_bindings=[("q", quit_debugger)])

        if result == "quit":
            return

        pre_run = pre_run_edit.get_edit_text()

        dbg.restart()

    if args is not None:
        sys.argv = prev_sys_argv

    sys.path = prev_sys_path

def runstatement(statement, globals=None, locals=None):
    _get_debugger().run(statement, globals, locals)

def runeval(expression, globals=None, locals=None):
    return _get_debugger().runeval(expression, globals, locals)

def runcall(*args, **kwds):
    return _get_debugger().runcall(*args, **kwds)

def set_trace():
    import sys
    dbg = _get_debugger()

    from pudb.settings import load_breakpoints
    for bpoint_descr in load_breakpoints(dbg):
        dbg.set_break(*bpoint_descr)

    dbg.set_trace(sys._getframe().f_back)




def post_mortem(exc_info=None):
    if exc_info is None:
        import sys
        exc_info = sys.exc_info()

    tb = exc_info[2]
    while tb.tb_next is not None:
        tb = tb.tb_next

    dbg = _get_debugger()
    dbg.reset()
    dbg.interaction(tb.tb_frame, exc_info)




def pm():
    import sys
    try:
        e_type = sys.last_type
        e_value = sys.last_value
        tb = sys.last_traceback
    except AttributeError:
        ## No exception on record. Do nothing.
        return
    post_mortem((e_type, e_value, tb))




if __name__ == "__main__":
    print "You now need to type 'python -m pudb.run'. Sorry."
