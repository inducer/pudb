__copyright__ = """
Copyright (C) 2026 University of Illinois Board of Trustees
"""

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import io
import socket
import sys

import pytest

from pudb.debugger import Debugger, ThreadsafeFixedSizeRawScreen
from pudb.remote import RemoteDebugger, TelnetCharacters


@pytest.mark.parametrize("reverse", [False, True])
def test_remote_keyboard_input(monkeypatch: pytest.MonkeyPatch, reverse: bool) -> None:
    server, client = socket.socketpair()
    server.settimeout(1)
    client.settimeout(1)
    remote = None
    try:
        def get_client(
            self: RemoteDebugger, **_kwargs: object,
        ) -> tuple[socket.socket, tuple[str, int]]:
            self.host = "127.0.0.1"
            self.port = 6899
            self.ident = "pudb:6899"
            return server, (self.host, self.port)

        monkeypatch.setattr(RemoteDebugger, "get_client", get_client)

        def init_debugger(self: Debugger, **_kwargs: object) -> None:
            self._tty_file = None  # pyright: ignore[reportPrivateUsage]

        monkeypatch.setattr(Debugger, "__init__", init_debugger)

        if not reverse:
            tn = TelnetCharacters
            client.sendall(tn.IAC + tn.DO + tn.SGA + tn.IAC + tn.DO + tn.ECHO)

        remote = RemoteDebugger(out=io.StringIO(), reverse=reverse)
        screen = ThreadsafeFixedSizeRawScreen(
            input=sys.stdin, output=sys.stdout, term_size=(80, 24))
        screen.set_input_timeouts(max_wait=0.1)
        with screen.start():
            # A dynamically forwarded fileno() was invisible to Urwid's runtime
            # protocol checks on Python 3.12+, leaving only the resize socket.
            assert server.fileno() in [
                fd if isinstance(fd, int) else fd.fileno()
                for fd in screen.get_input_descriptors()
            ]
            client.sendall(b"q")
            assert screen.get_input(raw_keys=True) == (["q"], [ord("q")])
    finally:
        if remote is not None:
            remote.close_remote_session()
        server.close()
        client.close()
