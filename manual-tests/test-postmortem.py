def f():
    fail  # ruff:ignore[useless-expression, undefined-name]


try:
    f()
except Exception:
    from pudb import post_mortem
    post_mortem()
