def f():
    fail  # noqa: B018, F821


from pudb import runcall


runcall(f)
