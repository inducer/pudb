__copyright__ = """
Copyright (C) 2009-2017 Andreas Kloeckner
Copyright (C) 2014-2017 Aaron Meurer
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


import logging
import sys
from datetime import datetime


logfile = [None]


def getlogfile():
    return logfile[0]


def setlogfile(destfile):
    logfile[0] = destfile
    with open(destfile, "a") as openfile:
        openfile.write(
            "\n*** Pudb session error log started at {date} ***\n".format(
                date=datetime.now()
            ))


class TerminalOrStreamHandler(logging.StreamHandler):
    """
    Logging handler that sends errors either to the terminal window or to
    stderr, depending on whether the debugger is active.
    """
    def emit(self, record):
        from pudb import _get_debugger, _have_debugger
        logfile = getlogfile()

        self.acquire()
        try:
            if logfile is not None:
                message = self.format(record)
                with open(logfile, "a") as openfile:
                    openfile.write("\n%s\n" % message)
            elif _have_debugger():
                dbg = _get_debugger()
                message = self.format(record)
                dbg.ui.add_cmdline_content(message, "command line error")
            else:
                super().emit(record)
        finally:
            self.release()


def _init_loggers():
    ui_handler = TerminalOrStreamHandler()
    ui_formatter = logging.Formatter(
        fmt="*** Pudb UI Exception Encountered: %(message)s ***\n"
    )
    ui_handler.setFormatter(ui_formatter)
    ui_log = logging.getLogger("ui")
    ui_log.addHandler(ui_handler)

    settings_handler = TerminalOrStreamHandler()
    settings_formatter = logging.Formatter(
        fmt="*** Pudb Settings Exception Encountered: %(message)s ***\n"
    )
    settings_handler.setFormatter(settings_formatter)
    settings_log = logging.getLogger("settings")
    settings_log.addHandler(settings_handler)

    return ui_log, settings_log


ui_log, settings_log = _init_loggers()


# {{{ breakpoint validity

def generate_executable_lines_for_code(code):
    if sys.version_info >= (3, 10):
        for _start, _end, lineno in code.co_lines():
            if lineno is not None:
                yield lineno
    else:
        lineno = code.co_firstlineno
        yield lineno
        # See https://github.com/python/cpython/blob/master/Objects/lnotab_notes.txt

        for line_incr in code.co_lnotab[1::2]:
            # NB: This code is specific to Python 3.6 and higher
            # https://github.com/python/cpython/blob/v3.6.0/Objects/lnotab_notes.txt
            if line_incr >= 0x80:
                line_incr -= 0x100
            lineno += line_incr
            yield lineno


def get_executable_lines_for_codes_recursive(codes):
    codes = codes[:]

    from types import CodeType

    execable_lines = set()

    while codes:
        code = codes.pop()
        execable_lines |= set(generate_executable_lines_for_code(code))
        codes.extend(const
                for const in code.co_consts
                if isinstance(const, CodeType))

    return execable_lines


def get_executable_lines_for_file(filename):
    # inspired by rpdb2

    from linecache import getlines
    codes = [compile("".join(getlines(filename)), filename, "exec", dont_inherit=1)]

    return get_executable_lines_for_codes_recursive(codes)


def get_breakpoint_invalid_reason(filename, lineno):
    # simple logic stolen from pdb
    import linecache
    line = linecache.getline(filename, lineno)
    if not line:
        return "Line is beyond end of file."

    try:
        executable_lines = get_executable_lines_for_file(filename)
    except SyntaxError:
        return "File failed to compile."

    if lineno not in executable_lines:
        return "No executable statement found in line."


def lookup_module(filename):
    """Helper function for break/clear parsing -- may be overridden.

    lookupmodule() translates (possibly incomplete) file or module name
    into an absolute file name.
    """

    # stolen from pdb
    import os
    import sys

    if os.path.isabs(filename) and os.path.exists(filename):
        return filename
    f = os.path.join(sys.path[0], filename)
    if os.path.exists(f):  # and self.canonic(f) == self.mainpyfile:
        return f
    _root, ext = os.path.splitext(filename)
    if ext == "":
        filename = filename + ".py"
    if os.path.isabs(filename):
        return filename
    for dirname in sys.path:
        while os.path.islink(dirname):
            dirname = os.readlink(dirname)
        fullname = os.path.join(dirname, filename)
        if os.path.exists(fullname):
            return fullname
    return None

# }}}


# {{{ file encoding detection
# the main idea stolen from Python 3.1's tokenize.py, by Ka-Ping Yee

import re


cookie_re = re.compile(br"^\s*#.*coding[:=]\s*([-\w.]+)")
from codecs import BOM_UTF8, lookup


def detect_encoding(line_iter):
    """
    The detect_encoding() function is used to detect the encoding that should
    be used to decode a Python source file. It requires one argument, line_iter,
    an iterator on the lines to be read.

    It will read a maximum of two lines, and return the encoding used
    (as a string) and a list of any lines (left as bytes) it has read
    in.

    It detects the encoding from the presence of a utf-8 bom or an encoding
    cookie as specified in pep-0263. If both a bom and a cookie are present,
    but disagree, a SyntaxError will be raised. If the encoding cookie is an
    invalid charset, raise a SyntaxError.

    If no encoding is specified, then the default of 'utf-8' will be returned.
    """
    bom_found = False

    def read_or_stop():
        try:
            return next(line_iter)
        except StopIteration:
            return ""

    def find_cookie(line):
        try:
            line_string = line
        except UnicodeDecodeError:
            return None

        matches = cookie_re.findall(line_string)
        if not matches:
            return None
        encoding = matches[0].decode()
        try:
            codec = lookup(encoding)
        except LookupError as err:
            # This behaviour mimics the Python interpreter
            raise SyntaxError("unknown encoding: " + encoding) from err

        if bom_found and codec.name != "utf-8":
            # This behaviour mimics the Python interpreter
            raise SyntaxError("encoding problem: utf-8")
        return encoding

    first = read_or_stop()
    if isinstance(first, str):
        return None, [first]

    if first.startswith(BOM_UTF8):
        bom_found = True
        first = first[3:]
    if not first:
        return "utf-8", []

    encoding = find_cookie(first)
    if encoding:
        return encoding, [first]

    second = read_or_stop()
    if not second:
        return "utf-8", [first]

    encoding = find_cookie(second)
    if encoding:
        return encoding, [first, second]

    return "utf-8", [first, second]


def decode_lines(lines):
    line_iter = iter(lines)
    source_enc, detection_read_lines = detect_encoding(line_iter)

    from itertools import chain

    for line in chain(detection_read_lines, line_iter):
        if hasattr(line, "decode") and source_enc is not None:
            yield line.decode(source_enc)
        else:
            yield line

# }}}


# {{{ non-buffered console

# Local platform dependent helper to get single key presses from a
# terminal in unbuffered mode. Eliminates the necessity to press ENTER
# before other input also becomes available. Also avoids the accumulation
# of prompts on the screen as was the case with Python's input() call.
# Is used in situations where urwid is disabled and curses calls are
# not available.

( _NBC_IMPL_INPUT, _NBC_IMPL_GETCH, _NBC_IMPL_SELECT, ) = range(3)
_nbc_impl = _NBC_IMPL_INPUT
if sys.platform in ("emscripten", "wasi"):
    pass
elif sys.platform in ("win32",):
    import msvcrt
    _nbc_impl = _NBC_IMPL_GETCH
else:
    import select
    import termios
    import tty
    _nbc_impl = _NBC_IMPL_SELECT


class NonBufferedConsole(object):

    def __init__(self):
        pass

    def __enter__(self):
        if _nbc_impl == _NBC_IMPL_SELECT:
            self.prev_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, type, value, traceback):
        if _nbc_impl == _NBC_IMPL_SELECT:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.prev_settings)

    def get_data(self):
        if _nbc_impl == _NBC_IMPL_GETCH:
            c = msvcrt.getch()
            if c in ('\x00', '\xe0'):
                c = msvcrt.getch()
            return c

        elif _nbc_impl == _NBC_IMPL_SELECT:
            rset, _, _ = select.select([sys.stdin], [], [], None)
            assert sys.stdin in rset
            return sys.stdin.read(1)

        # Strictly speaking putting the fallback here which requires
        # pressing ENTER is not correct, this is the "non buffered"
        # console support code. But it simplifies call sites. And is
        # easy to tell by users because a prompt is provided. This is
        # the most portable approach, and backwards compatible with
        # earlier PuDB releases. It's a most appropriate default for
        # otherwise unsupported platforms. Or when users choose to
        # not accept single key presses, or keys other than ENTER.
        else:
            input("Hit Enter to return:")
            return None

# }}}

# vim: foldmethod=marker
