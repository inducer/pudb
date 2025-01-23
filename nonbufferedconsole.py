"""
Evaluation script for non-buffered console operation and the portability
of the implementation across Python supported platforms. Can be executed
on any computer that has Python available. Does not depend on 3rd party
libraries, exclusively uses core features.
"""

from enum import Enum, auto
import sys

class KeyReadImpl(Enum):
	INPUT = auto()
	GETCH = auto()
	SELECT = auto()

_keyread_impl = KeyReadImpl.INPUT

if sys.platform in ("emscripten", "wasi"):
	pass
elif sys.platform in ("win32",):
	_keyread_impl = KeyReadImpl.GETCH
else:
	_keyread_impl = KeyReadImpl.SELECT

class ConsoleSingleKeyReader:

	def __enter__(self):
		if _keyread_impl == KeyReadImpl.SELECT:
			import termios
			import tty
			self.prev_settings = termios.tcgetattr(sys.stdin)
			tty.setcbreak(sys.stdin.fileno())
		return self

	def __exit__(self, type, value, traceback):
		if _keyread_impl == KeyReadImpl.SELECT:
			import termios
			termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.prev_settings)

	def get_single_key(self):
		if _keyread_impl == KeyReadImpl.GETCH:
			import msvcrt
			c = msvcrt.getch()
			if c in ('\x00', '\xe0'):
				c = msvcrt.getch()
			return c

		elif _keyread_impl == KeyReadImpl.SELECT:
			import select
			rset, _, _ = select.select([sys.stdin], [], [], None)
			assert sys.stdin in rset
			return sys.stdin.read(1)

		# The Python input() call strictly speaking is not a
		# terminal in non-buffered mode and without a prompt.
		# But supporting this fallback here is most appropriate
		# and simplifies call sites.
		else:
			input("Hit Enter to return:")
			return None

if __name__ == "__main__":
	print("waiting for key press")
	with ConsoleSingleKeyReader() as keyreader:
		keyreader.get_single_key()
	print("key press seen")
