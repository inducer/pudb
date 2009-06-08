def fermat(n):
    """Returns triplets of the form x^n + y^n = z^n.
    Warning! Untested with n > 2.
    """
    from itertools import count
    for x in count(1):
        for y in range(1, x+1):
            for z in range(1, x**n+y**n + 1):
                if x**n + y**n == z**n:
                    yield x, y, z

for i in fermat(2):
    print i

