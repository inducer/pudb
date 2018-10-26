from __future__ import absolute_import, division, print_function

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


from pudb.py3compat import PY3, text_type


# {{{ breakpoint validity

def generate_executable_lines_for_code(code):
    lineno = code.co_firstlineno
    yield lineno
    if PY3:
        for c in code.co_lnotab[1::2]:
            lineno += c
            yield lineno
    else:
        for c in code.co_lnotab[1::2]:
            lineno += ord(c)
            yield lineno


def get_executable_lines_for_file(filename):
    # inspired by rpdb2

    from linecache import getlines
    codes = [compile("".join(getlines(filename)), filename, "exec", dont_inherit=1)]

    from types import CodeType

    execable_lines = set()

    while codes:
        code = codes.pop()
        execable_lines |= set(generate_executable_lines_for_code(code))
        codes.extend(const
                for const in code.co_consts
                if isinstance(const, CodeType))

    return execable_lines


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
    root, ext = os.path.splitext(filename)
    if ext == '':
        filename = filename + '.py'
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
from codecs import lookup, BOM_UTF8


def detect_encoding(line_iter):
    """
    The detect_encoding() function is used to detect the encoding that should
    be used to decode a Python source file. It requires one argment, line_iter,
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
            return ''

    def find_cookie(line):
        try:
            if PY3:
                line_string = line
            else:
                line_string = line.decode('ascii')
        except UnicodeDecodeError:
            return None

        matches = cookie_re.findall(line_string)
        if not matches:
            return None
        encoding = matches[0].decode()
        try:
            codec = lookup(encoding)
        except LookupError:
            # This behaviour mimics the Python interpreter
            raise SyntaxError("unknown encoding: " + encoding)

        if bom_found and codec.name != 'utf-8':
            # This behaviour mimics the Python interpreter
            raise SyntaxError('encoding problem: utf-8')
        return encoding

    first = read_or_stop()
    if isinstance(first, text_type):
        return None, [first]

    if first.startswith(BOM_UTF8):
        bom_found = True
        first = first[3:]
    if not first:
        return 'utf-8', []

    encoding = find_cookie(first)
    if encoding:
        return encoding, [first]

    second = read_or_stop()
    if not second:
        return 'utf-8', [first]

    encoding = find_cookie(second)
    if encoding:
        return encoding, [first, second]

    return 'utf-8', [first, second]


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


# {{{ traceback formatting

class StringExceptionValueWrapper:
    def __init__(self, string_val):
        self.string_val = string_val

    def __str__(self):
        return self.string_val

    __context__ = None
    __cause__ = None


def format_exception(exc_tuple):
    # Work around http://bugs.python.org/issue17413
    # See also https://github.com/inducer/pudb/issues/61

    from traceback import format_exception
    if PY3:
        exc_type, exc_value, exc_tb = exc_tuple

        if isinstance(exc_value, str):
            exc_value = StringExceptionValueWrapper(exc_value)
            exc_tuple = exc_type, exc_value, exc_tb

        return format_exception(
                *exc_tuple,
                **dict(chain=hasattr(exc_value, "__context__")))
    else:
        return format_exception(*exc_tuple)

# }}}

# vim: foldmethod=marker
