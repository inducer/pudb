VERSION = "0.91"




CURRENT_DEBUGGER = [None]
def set_trace():
    if CURRENT_DEBUGGER[0] is None:
        from pudb.debugger import Debugger
        dbg = Debugger()
        CURRENT_DEBUGGER[0] = dbg

        import sys
        dbg.set_trace(sys._getframe().f_back)




def post_mortem(t):
    p = Debugger()
    p.reset()
    while t.tb_next is not None:
        t = t.tb_next
    p.interaction(t.tb_frame, t)




def pm():
    import sys
    post_mortem(sys.last_traceback)




def main():
    import sys
    if not sys.argv[1:]:
        print "usage: %s scriptfile [-s] [arg] ..." % sys.argv[0]
        sys.exit(2)

    mainpyfile =  sys.argv[1]
    from os.path import exists, dirname
    if not exists(mainpyfile):
        print 'Error:', mainpyfile, 'does not exist'
        sys.exit(1)

    # Hide "pudb.py" from argument list
    del sys.argv[0]

    steal_output = sys.argv[0] == "-s"
    if steal_output:
        del sys.argv[0]

    # Replace pdb's dir with script's dir in front of module search path.
    sys.path[0] = dirname(mainpyfile)

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user from the command line. The best approach would be to
    # have a "restart" command which would allow explicit specification of
    # command line arguments.

    from os import getpid

    start_pid = getpid()

    from pudb.debugger import Debugger
    dbg = Debugger(steal_output=steal_output)

    while True:
        status_msg = ""
        try:
            dbg._runscript(mainpyfile)
        except SystemExit, se:
            status_msg = "The debuggee exited normally with status code was %d.\n\n" % se.code
        except:
            dbg.post_mortem = True
            dbg.interaction(None, sys.exc_info())

        if getpid() == start_pid:
            import urwid
            result = dbg.ui.call_with_ui(dbg.ui.dialog,
                urwid.ListBox([urwid.Text(
                    "Your PuDB session has ended.\n\n%s"
                    "Would you like to quit PuDB or restart your program?"
                    % status_msg)]),
                [
                    ("Restart", "restart"),
                    ("Quit", "quit"),
                    ],
                focus_buttons=True,
                title="Finished")

            if result == "quit":
                return
        else:
            return

        dbg.restart()



if __name__=='__main__':
    main()
