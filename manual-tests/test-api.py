def f():
    fail  # ruff:ignore[useless-expression, undefined-name]


from pudb import runcall


runcall(f)
