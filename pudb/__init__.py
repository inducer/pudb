VERSION = "0.91.2"




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
