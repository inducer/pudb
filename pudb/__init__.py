VERSION = "0.91.4"




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




if __name__ == "__main__":
    print "To keep Python 2.6 happy, you now need to type 'python -m pudb.run'."
    print "Sorry for the inconvenience."
