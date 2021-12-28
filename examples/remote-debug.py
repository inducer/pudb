def debugged_function(x):
    y = x + fail  # noqa: F821
    return y


from pudb.remote import debugger
dbg = debugger()
dbg.runcall(debugged_function, 5)
