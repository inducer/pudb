def simple_func(x):
    x += 1
    return 2*x

def fermat(n):
    """Returns triplets of the form x^n + y^n = z^n.
    Warning! Untested with n > 2.
    """
    from itertools import count
    for x in count(1):
        for y in range(1, x+1):
            for z in range(1, x**n+y**n + 1):
                from pudb import set_trace; set_trace()
                if x**n + y**n == z**n:
                    yield x, y, z

print "SF", simple_func(10)

for i in fermat(2):
    print i

