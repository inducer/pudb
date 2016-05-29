def f(encoding=None):
	print 'ENCODING:', encoding

from pudb import runcall
runcall(f)
