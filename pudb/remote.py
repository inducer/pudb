"""
.. autoclass:: RemoteDebugger

.. autofunction:: set_trace
.. autofunction:: debugger
.. autofunction:: debug_remote_on_single_rank
.. autofunction:: post_mortem
.. autofunction:: pm
"""
from __future__ import annotations


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

import atexit
import errno
import os
import socket
import sys
from typing import (
    TYPE_CHECKING,
    Callable,
    ClassVar,
    TextIO,
    TypeVar,
)

from typing_extensions import ParamSpec

from pudb.debugger import Debugger, OptExcInfo


if TYPE_CHECKING:
    from types import FrameType, TracebackType

    from mpi4py import MPI


P = ParamSpec("P")
ResultT = TypeVar("ResultT")


__all__ = [
    "PUDB_RDB_HOST",
    "PUDB_RDB_PORT",
    "PUDB_RDB_REVERSE",
    "debug_remote_on_single_rank",
    "debugger",
    "default_port",
    "pm",
    "post_mortem",
    "set_trace",
]

default_port = 6899

PUDB_RDB_HOST = os.environ.get("PUDB_RDB_HOST") or "127.0.0.1"
PUDB_RDB_PORT = int(os.environ.get("PUDB_RDB_PORT") or default_port)
PUDB_RDB_REVERSE = bool(os.environ.get("PUDB_RDB_REVERSE"))


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


class TelnetCharacters:
    """Collection of characters from the telnet protocol RFC 854

    This format for the telnet characters was adapted from the telnetlib module
    which was removed from the C Python standard library in version 3.13. Only
    the characters needed by pudb have been copied here. Additional characters
    can be found by looking in the telnetlib code in Python 3.12 or in the
    telnet RFC.

    .. note::

        This class is not intended to be instantiated.
    """
    # Telnet protocol characters
    IAC: ClassVar[bytes] = b"\xff"  # "Interpret As Command"
    DO: ClassVar[bytes] = b"\xfd"
    WILL: ClassVar[bytes] = b"\xfb"

    # Telnet protocol options codes
    # These ones all come from arpa/telnet.h
    ECHO: ClassVar[bytes] = b"\x01"  # echo
    SGA: ClassVar[bytes] = b"\x03"  # suppress go ahead


class RemoteDebugger(Debugger):
    """
    .. automethod:: __init__
    """

    me: ClassVar[str] = "pudb"

    _sock: socket.socket | None = None
    _client: socket.socket
    _prev_handles: tuple[TextIO, TextIO]
    out: TextIO
    _handle: TextIO
    remote_addr: str

    host: str  # pyright: ignore[reportUninitializedInstanceVariable]
    port: int  # pyright: ignore[reportUninitializedInstanceVariable]

    def __init__(
        self,
        host: str = PUDB_RDB_HOST,
        port: int = PUDB_RDB_PORT,
        port_search_limit: int = 100,
        out: TextIO = sys.stdout,
        term_size: tuple[int, int]  | None = None,
        reverse: bool = PUDB_RDB_REVERSE,
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
            term_size_str = os.environ.get("PUDB_TERM_SIZE")
            if term_size_str is not None:
                term_size_tup = tuple(map(int, term_size_str.split("x")))
                if len(term_size_tup) != 2:
                    raise ValueError("PUDB_TERM_SIZE should have two dimensions")
                term_size = term_size_tup
            else:
                try:
                    s = os.get_terminal_size()
                    term_size = (s.columns, s.lines)
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
            tn = TelnetCharacters

            raw_sock_file.write(tn.IAC + tn.WILL + tn.SGA)
            resp = raw_sock_file.read(3)
            assert resp == tn.IAC + tn.DO + tn.SGA

            raw_sock_file.write(tn.IAC + tn.WILL + tn.ECHO)
            resp = raw_sock_file.read(3)
            assert resp == tn.IAC + tn.DO + tn.ECHO

        Debugger.__init__(
            self, stdin=self._handle, stdout=self._handle, term_size=term_size
        )

    def get_client(self,
                host: str,
                port: int,
                search_limit: int = 100,
                reverse: bool = False
            ) -> tuple[socket.socket, tuple[str, int]]:
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
        client.setblocking(True)
        return client, (address, self.port)

    def get_reverse_socket_client(self, host: str, port: int):
        sock = socket.socket()
        try:
            sock.connect((host, port))
            sock.setblocking(True)
        except OSError as exc:
            if exc.errno == errno.ECONNREFUSED:
                raise ValueError(CONN_REFUSED.format(self=self)) from exc
            raise exc
        return sock, sock.getpeername()

    def get_socket_client(self, host: str, port: int, search_limit: int):
        sock, this_port = self.get_avail_port(host, port, search_limit)
        sock.setblocking(True)
        sock.listen(1)
        return sock, (host, this_port)

    def get_avail_port(self, host: str, port: int, search_limit: int = 100):
        this_port = None
        for i in range(search_limit):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            this_port = port + i
            try:
                sock.bind((host, this_port))
            except OSError as exc:
                if exc.errno in [errno.EADDRINUSE, errno.EINVAL]:
                    continue
                raise
            else:
                return sock, this_port
        else:
            raise Exception(NO_AVAILABLE_PORT.format(self=self))

    def say(self, m: str):
        print(m, file=self.out)

    def close_remote_session(self):
        sys.stdin, sys.stdout = self._prev_handles
        self._handle.close()
        self._client.close()
        if self._sock:
            self._sock.close()
        self.say(SESSION_ENDED.format(self=self))


def debugger(
    term_size: tuple[int, int] | None = None,
    host=PUDB_RDB_HOST,
    port=PUDB_RDB_PORT,
    reverse=PUDB_RDB_REVERSE
):
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
    frame: FrameType | None = None,
    term_size: tuple[int, int] | None = None,
    host: str = PUDB_RDB_HOST,
    port: int = PUDB_RDB_PORT,
    reverse: bool = PUDB_RDB_REVERSE
):
    """Set breakpoint at current location, or a specified frame"""
    if frame is None:
        frame = _frame().f_back

    return debugger(
        term_size=term_size, host=host, port=port, reverse=reverse
    ).set_trace(frame)


def post_mortem(
            exc_tuple: OptExcInfo | TracebackType | None = None,
            term_size: tuple[int, int] | None = None,
            host: str = PUDB_RDB_HOST,
            port: int = PUDB_RDB_PORT,
            reverse: bool = PUDB_RDB_REVERSE
        ):
    """Start a debugger on a given traceback object."""
    dbg = debugger(term_size=term_size, host=host, port=port, reverse=reverse)
    dbg.reset()
    dbg.interaction(None, exc_tuple or sys.exc_info())


pm = post_mortem


def debug_remote_on_single_rank(
            comm: MPI.Intracomm,
            rank: int,
            func: Callable[P, ResultT],
            *args: P.args,
            **kwargs: P.kwargs) -> None:
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
