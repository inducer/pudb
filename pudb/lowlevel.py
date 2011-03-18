# breakpoint validity ---------------------------------------------------------
def generate_executable_lines_for_code(code):
    l = code.co_firstlineno
    yield l
    for c in code.co_lnotab[1::2]:
        l += ord(c)
        yield l




def get_executable_lines_for_file(filename):
    # inspired by rpdb2

    from linecache import getlines
    codes = [compile("".join(getlines(filename)), filename, "exec")]

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

    if lineno not in get_executable_lines_for_file(filename):
        return "No executable statement found in line."



def lookup_module(filename):
    """Helper function for break/clear parsing -- may be overridden.

    lookupmodule() translates (possibly incomplete) file or module name
    into an absolute file name.
    """

    # stolen from pdb
    import os, sys

    if os.path.isabs(filename) and  os.path.exists(filename):
        return filename
    f = os.path.join(sys.path[0], filename)
    if  os.path.exists(f): # and self.canonic(f) == self.mainpyfile:
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




# file encoding detection -----------------------------------------------------
# stolen from Python 3.1's tokenize.py, by Ka-Ping Yee

import re
cookie_re = re.compile("coding[:=]\s*([-\w.]+)")
from codecs import lookup, BOM_UTF8

def detect_encoding(readline):
    """
    The detect_encoding() function is used to detect the encoding that should
    be used to decode a Python source file. It requires one argment, readline,
    in the same way as the tokenize() generator.

    It will call readline a maximum of twice, and return the encoding used
    (as a string) and a list of any lines (left as bytes) it has read
    in.

    It detects the encoding from the presence of a utf-8 bom or an encoding
    cookie as specified in pep-0263. If both a bom and a cookie are present,
    but disagree, a SyntaxError will be raised. If the encoding cookie is an
    invalid charset, raise a SyntaxError.

    If no encoding is specified, then the default of 'utf-8' will be returned.
    """
    bom_found = False
    encoding = None
    def read_or_stop():
        try:
            return readline()
        except StopIteration:
            return ''

    def find_cookie(line):
        try:
            line_string = line.decode('ascii')
        except UnicodeDecodeError:
            return None

        matches = cookie_re.findall(line_string)
        if not matches:
            return None
        encoding = matches[0]
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
