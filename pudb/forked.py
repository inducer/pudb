# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals


import sys
import fcntl
import termios
import struct

from pudb.debugger import Debugger

def forked_pudb():
    frame = sys._getframe().f_back
    try:
        # Getting terminal size
        s = struct.unpack(
            "hh",
            fcntl.ioctl(1, termios.TIOCGWINSZ, "1234"),
        )
        term_size = (s[1], s[0])
    except Exception:
        term_size = (80, 24)

    Debugger(
        stdin=open("/dev/stdin"), stdout=open("/dev/stdout", "w"), term_size=term_size
    ).set_trace(frame)
