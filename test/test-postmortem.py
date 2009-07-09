def f():
    fail

try:
    f()
except:
    from pudb import post_mortem
    post_mortem()
