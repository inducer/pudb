def debugged_function(x):
    return x + fail  # noqa: F821


from pudb.remote import debugger


dbg = debugger()
dbg.runcall(debugged_function, 5)
