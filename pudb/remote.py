# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

# mostly stolen from celery.contrib.rdb


import errno
import os
import socket
import sys

from pudb.debugger import Debugger

__all__ = ['PUDB_RDB_HOST', 'PUDB_RDB_PORT', 'default_port',
           'debugger', 'set_trace']

default_port = 6899

PUDB_RDB_HOST = os.environ.get('PUDB_RDB_HOST') or '127.0.0.1'
PUDB_RDB_PORT = int(os.environ.get('PUDB_RDB_PORT') or default_port)

#: Holds the currently active debugger.
_current = [None]

_frame = getattr(sys, '_getframe')

NO_AVAILABLE_PORT = """\
{self.ident}: Couldn't find an available port.

Please specify one using the PUDB_RDB_PORT environment variable.
"""

BANNER = """\
{self.ident}: Please telnet into {self.host} {self.port}.
{self.ident}: Waiting for client...
"""

SESSION_STARTED = '{self.ident}: Now in session with {self.remote_addr}.'
SESSION_ENDED = '{self.ident}: Session with {self.remote_addr} ended.'


class RemoteDebugger(Debugger):
    me = 'pudb'
    _prev_outs = None
    _sock = None

    def __init__(self, host=PUDB_RDB_HOST, port=PUDB_RDB_PORT,
                 port_search_limit=100, out=sys.stdout, term_size=None):
        self.active = True
        self.out = out

        self._prev_handles = sys.stdin, sys.stdout

        self._sock, this_port = self.get_avail_port(
            host, port, port_search_limit)
        self._sock.setblocking(1)
        self._sock.listen(1)
        self.ident = '{0}:{1}'.format(self.me, this_port)
        self.host = host
        self.port = this_port
        self.say(BANNER.format(self=self))

        self._client, address = self._sock.accept()
        self._client.setblocking(1)
        self.remote_addr = ':'.join(str(v) for v in address)
        self.say(SESSION_STARTED.format(self=self))

        # makefile ignores encoding if there's no buffering.
        raw_sock_file = self._client.makefile("rwb", 0)
        import codecs
        sock_file = codecs.StreamReaderWriter(raw_sock_file,
                codecs.getreader("utf-8"),
                codecs.getwriter("utf-8"))

        self._handle = sys.stdin = sys.stdout = sock_file

        import telnetlib as tn

        raw_sock_file.write(tn.IAC + tn.WILL + tn.SGA)
        resp = raw_sock_file.read(3)
        assert resp == tn.IAC + tn.DO + tn.SGA

        raw_sock_file.write(tn.IAC + tn.WILL + tn.ECHO)
        resp = raw_sock_file.read(3)
        assert resp == tn.IAC + tn.DO + tn.ECHO

        Debugger.__init__(self, stdin=self._handle, stdout=self._handle,
                term_size=term_size)

    def get_avail_port(self, host, port, search_limit=100, skew=+0):
        this_port = None
        for i in range(search_limit):
            _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            this_port = port + i
            try:
                _sock.bind((host, this_port))
            except socket.error as exc:
                if exc.errno in [errno.EADDRINUSE, errno.EINVAL]:
                    continue
                raise
            else:
                return _sock, this_port
        else:
            raise Exception(NO_AVAILABLE_PORT.format(self=self))

    def say(self, m):
        print(m, file=self.out)

    def _close_session(self):
        self.stdin, self.stdout = sys.stdin, sys.stdout = self._prev_handles
        self._handle.close()
        self._client.close()
        self._sock.close()
        self.active = False
        self.say(SESSION_ENDED.format(self=self))

    def do_continue(self, arg):
        self._close_session()
        self.set_continue()
        return 1
    do_c = do_cont = do_continue

    def do_quit(self, arg):
        self._close_session()
        self.set_quit()
        return 1

    def set_quit(self):
        # this raises a BdbQuit exception that we are unable to catch.
        sys.settrace(None)


def debugger(term_size=None, host=PUDB_RDB_HOST, port=PUDB_RDB_PORT):
    """Return the current debugger instance (if any),
    or creates a new one."""
    rdb = _current[0]
    if rdb is None or not rdb.active:
        rdb = _current[0] = RemoteDebugger(host=host, port=port, term_size=term_size)
    return rdb


def set_trace(frame=None, term_size=None, host=PUDB_RDB_HOST, port=PUDB_RDB_PORT):
    """Set breakpoint at current location, or a specified frame"""
    if frame is None:
        frame = _frame().f_back
    return debugger(term_size=term_size, host=host, port=port).set_trace(frame)
