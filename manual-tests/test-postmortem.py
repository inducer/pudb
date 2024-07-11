def f():
    fail  # noqa: B018, F821


try:
    f()
except Exception:
    from pudb import post_mortem
    post_mortem()
