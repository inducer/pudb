def f():
    fail

from pudb import runcall
runcall(f)
