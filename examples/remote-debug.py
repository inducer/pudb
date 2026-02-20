def debugged_function(x):
    return x + 1/0


from pudb.remote import debugger


dbg = debugger()
dbg.runcall(debugged_function, 5)
