"""
.. autoclass:: RemoteDebugger

.. autofunction:: set_trace
.. autofunction:: debugger
.. autofunction:: debug_remote_on_single_rank
"""

__copyright__ = """
Copyright (C) 2009-2017 Andreas Kloeckner
Copyright (C) 2014-2017 Aaron Meurer
Copyright (C) 2020-2020 Son Geon
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


# mostly stolen from celery.contrib.rdb


import errno
import os
import socket
import sys
import fcntl
import termios
import struct
import atexit
from typing import Callable, Any

from pudb.debugger import Debugger

__all__ = ["PUDB_RDB_HOST", "PUDB_RDB_PORT", "default_port", "debugger", "set_trace",
           "debug_remote_on_single_rank"]

default_port = 6899

PUDB_RDB_HOST = os.environ.get("PUDB_RDB_HOST") or "127.0.0.1"
PUDB_RDB_PORT = int(os.environ.get("PUDB_RDB_PORT") or default_port)

#: Holds the currently active debugger.
_current = [None]

_frame = sys._getframe

NO_AVAILABLE_PORT = """\
{self.ident}: Couldn't find an available port.

Please specify one using the PUDB_RDB_PORT environment variable.
"""

BANNER = """\
{self.ident}: Please start a telnet session using a command like:
telnet {self.host} {self.port}
{self.ident}: Waiting for client...
"""

SESSION_STARTED = "{self.ident}: Now in session with {self.remote_addr}."
SESSION_ENDED = "{self.ident}: Session with {self.remote_addr} ended."

CONN_REFUSED = """\
Cannot connect to the reverse telnet client {self.host} {self.port}.

Try to open reverse client by running
stty -echo -icanon && nc -l -p 6899  # Linux
stty -echo -icanon && nc -l 6899  # BSD/MacOS

Please specify one using the PUDB_RDB_PORT environment variable.
"""


class RemoteDebugger(Debugger):
    """
    .. automethod:: __init__
    """

    me = "pudb"
    _prev_outs = None
    _sock = None

    def __init__(
        self,
        host=PUDB_RDB_HOST,
        port=PUDB_RDB_PORT,
        port_search_limit=100,
        out=sys.stdout,
        term_size=None,
        reverse=False,
    ):
        """
        :arg term_size: A two-tuple ``(columns, rows)``, or *None*. If *None*,
            try to determine the terminal size automatically.

            Currently, this uses a heuristic: It uses the terminal size of the
            debuggee as that for the debugger. The idea is that you might be
            running both in two tabs of the same terminal window, hence using
            terminals of the same size.
        """
        self.out = out

        if term_size is None:
            try:
                s = struct.unpack("hh", fcntl.ioctl(1, termios.TIOCGWINSZ, "1234"))
                term_size = (s[1], s[0])
            except Exception:
                term_size = (80, 24)

        self._prev_handles = sys.stdin, sys.stdout
        self._client, (address, port) = self.get_client(
            host=host, port=port, search_limit=port_search_limit, reverse=reverse
        )
        self.remote_addr = ":".join(str(v) for v in address)

        self.say(SESSION_STARTED.format(self=self))

        # makefile ignores encoding if there's no buffering.
        raw_sock_file = self._client.makefile("rwb", 0)
        import codecs

        sock_file = codecs.StreamReaderWriter(
            raw_sock_file, codecs.getreader("utf-8"), codecs.getwriter("utf-8"))

        self._handle = sys.stdin = sys.stdout = sock_file

        # nc negotiation doesn't support telnet options
        if not reverse:
            import telnetlib as tn

            raw_sock_file.write(tn.IAC + tn.WILL + tn.SGA)
            resp = raw_sock_file.read(3)
            assert resp == tn.IAC + tn.DO + tn.SGA

            raw_sock_file.write(tn.IAC + tn.WILL + tn.ECHO)
            resp = raw_sock_file.read(3)
            assert resp == tn.IAC + tn.DO + tn.ECHO

        Debugger.__init__(
            self, stdin=self._handle, stdout=self._handle, term_size=term_size
        )

    def get_client(self, host, port, search_limit=100, reverse=False):
        if reverse:
            self.host, self.port = host, port
            client, address = self.get_reverse_socket_client(host, port)
            self.ident = f"{self.me}:{self.port}"
        else:
            self._sock, conn_info = self.get_socket_client(
                host, port, search_limit=search_limit,
            )
            self.host, self.port = conn_info
            self.ident = f"{self.me}:{self.port}"
            self.say(BANNER.format(self=self))
            client, address = self._sock.accept()
        client.setblocking(1)
        return client, (address, self.port)

    def get_reverse_socket_client(self, host, port):
        _sock = socket.socket()
        try:
            _sock.connect((host, port))
            _sock.setblocking(1)
        except OSError as exc:
            if exc.errno == errno.ECONNREFUSED:
                raise ValueError(CONN_REFUSED.format(self=self))
            raise exc
        return _sock, _sock.getpeername()

    def get_socket_client(self, host, port, search_limit):
        _sock, this_port = self.get_avail_port(host, port, search_limit)
        _sock.setblocking(1)
        _sock.listen(1)
        return _sock, (host, this_port)

    def get_avail_port(self, host, port, search_limit=100, skew=+0):
        this_port = None
        for i in range(search_limit):
            _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            this_port = port + i
            try:
                _sock.bind((host, this_port))
            except OSError as exc:
                if exc.errno in [errno.EADDRINUSE, errno.EINVAL]:
                    continue
                raise
            else:
                return _sock, this_port
        else:
            raise Exception(NO_AVAILABLE_PORT.format(self=self))

    def say(self, m):
        print(m, file=self.out)

    def close_remote_session(self):
        self.stdin, self.stdout = sys.stdin, sys.stdout = self._prev_handles
        self._handle.close()
        self._client.close()
        if self._sock:
            self._sock.close()
        self.say(SESSION_ENDED.format(self=self))


def debugger(term_size=None, host=PUDB_RDB_HOST, port=PUDB_RDB_PORT, reverse=False):
    """Return the current debugger instance (if any),
    or creates a new one."""
    rdb = _current[0]
    if rdb is None:
        rdb = _current[0] = RemoteDebugger(
            host=host, port=port, term_size=term_size, reverse=reverse
        )
        atexit.register(lambda e: e.close_remote_session(), rdb)
    return rdb


def set_trace(
    frame=None, term_size=None, host=PUDB_RDB_HOST, port=PUDB_RDB_PORT, reverse=False
):
    """Set breakpoint at current location, or a specified frame"""
    if frame is None:
        frame = _frame().f_back

    return debugger(
        term_size=term_size, host=host, port=port, reverse=reverse
    ).set_trace(frame)


def debug_remote_on_single_rank(comm: Any, rank: int, func: Callable,
                                *args: Any, **kwargs: Any) -> None:
    """Run a remote debugger on a single rank of an ``mpi4py`` application.
    *func* will be called on rank *rank* running in a :class:`RemoteDebugger`,
    and will be called normally on all other ranks.

    :param comm: an ``mpi4py`` ``Comm`` object.
    :param rank: the rank to debug. All other ranks will spin until this rank exits.
    :param func: the callable to debug.
    :param args: the arguments passed to ``func``.
    :param kwargs: the kwargs passed to ``func``.
    """
    if comm.rank == rank:
        debugger().runcall(func, *args, **kwargs)
    else:
        try:
            func(*args, **kwargs)
        finally:
            from time import sleep
            while True:
                sleep(1)
