VERSION = "0.92.9"




CURRENT_DEBUGGER = []
def _get_debugger():
    if not CURRENT_DEBUGGER:
        from pudb.debugger import Debugger
        dbg = Debugger()
        CURRENT_DEBUGGER.append(dbg)
        return dbg
    else:
        return CURRENT_DEBUGGER[0]




def run(statement, globals=None, locals=None):
    _get_debugger().run(statement, globals, locals)

def runeval(expression, globals=None, locals=None):
    return _get_debugger().runeval(expression, globals, locals)

def runcall(*args, **kwds):
    return _get_debugger().runcall(*args, **kwds)

def set_trace():
    import sys
    _get_debugger().set_trace(sys._getframe().f_back)




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
    post_mortem(sys.last_traceback)




if __name__ == "__main__":
    print "You now need to type 'python -m pudb.run'. Sorry."
