class MyClass(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self._b = [b]

mc = MyClass(15, MyClass(12, None))


from pudb import set_trace; set_trace()

def simple_func(x):
    x += 1

    s = range(20)
    z = None
    w = ()

    y = dict((i, i**2) for i in s)

    k = set(range(5, 99))

    try:
        x.invalid
    except AttributeError:
        pass

    #import sys
    #sys.exit(1)

    return 2*x


def fermat(n):
    """Returns triplets of the form x^n + y^n = z^n.
    Warning! Untested with n > 2.
    """

    # source: "Fermat's last Python script"
    # https://earthboundkid.jottit.com/fermat.py
    # :)

    for x in range(100):
        for y in range(1, x+1):
            for z in range(1, x**n+y**n + 1):
                if x**n + y**n == z**n:
                    yield x, y, z

print("SF %s" % simple_func(10))

for i in fermat(2):
    print(i)

print("FINISHED")
