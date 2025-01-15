"""
Evaluation script for non-buffered console operation and the portability
of the implementation across Python supported platforms. Can be executed
on any computer that has Python available. Does not depend on 3rd party
libraries, exclusively uses core features.
"""

_nbc_use_input = True
_nbc_use_getch = False
_nbc_use_select = False

import sys
if sys.platform in ("emscripten", "wasi"):
	pass
elif sys.platform in ("win32",):
	import msvcrt
	_nbc_use_input = False
	_nbc_use_getch = True
else:
	import select
	import termios
	import tty
	_nbc_use_input = False
	_nbc_use_select = True

class NonBufferedConsole(object):

	def __init__(self):
		pass

	def __enter__(self):
		if _nbc_use_select:
			self.prev_settings = termios.tcgetattr(sys.stdin)
			tty.setcbreak(sys.stdin.fileno())
		return self

	def __exit__(self, type, value, traceback):
		if _nbc_use_select:
			termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.prev_settings)

	def get_data(self):
		if _nbc_use_getch:
			c = msvcrt.getch()
			if c in ('\x00', '\xe0'):
				c = msvcrt.getch()
			return c

		if _nbc_use_select:
			rset, _, _ = select.select([sys.stdin], [], [], None)
			if sys.stdin in rset:
				return sys.stdin.read(1)
			return None

		# The Python input() call strictly speaking is not a
		# terminal in non-buffered mode and without a prompt.
		# But supporting this fallback here is most appropriate
		# and simplifies call sites.
		if _nbc_use_input:
			input("Hit Enter to return:")
		return None

if __name__ == "__main__":
	print("waiting for key press")
	with NonBufferedConsole() as nbc:
		key = nbc.get_data()
	print("key press seen")
