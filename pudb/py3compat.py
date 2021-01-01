from __future__ import absolute_import, division, print_function
import sys

PY3 = sys.version_info[0] >= 3
if PY3:
    raw_input = input
    xrange = range
    integer_types = (int,)
    string_types = (str,)
    text_type = str

    def execfile(fname, globs, locs=None):
        exec(compile(open(fname).read(), fname, "exec"), globs, locs or globs)

    # {{{ container metaclasses

    from abc import ABC

    class PudbCollection(ABC):
        @classmethod
        def __subclasshook__(cls, C):
            if cls is PudbCollection:
                return all([
                    any("__contains__" in B.__dict__ for B in C.__mro__),
                    any("__iter__" in B.__dict__ for B in C.__mro__),
                ])
            return NotImplemented

    class PudbSequence(ABC):
        @classmethod
        def __subclasshook__(cls, C):
            if cls is PudbSequence:
                return all([
                    any("__getitem__" in B.__dict__ for B in C.__mro__),
                    any("__iter__" in B.__dict__ for B in C.__mro__),
                ])
            return NotImplemented

    class PudbMapping(ABC):
        @classmethod
        def __subclasshook__(cls, C):
            if cls is PudbMapping:
                return all([
                    any("__getitem__" in B.__dict__ for B in C.__mro__),
                    any("__iter__" in B.__dict__ for B in C.__mro__),
                    any("keys" in B.__dict__ for B in C.__mro__),
                ])
            return NotImplemented
    # }}}

else:
    raw_input = raw_input
    xrange = xrange
    integer_types = (int, long)  # noqa: F821
    string_types = (basestring,)  # noqa: F821
    text_type = unicode  # noqa: F821
    execfile = execfile

    # {{{ container metaclasses

    from abc import ABCMeta

    class PudbCollection:
        __metaclass__ = ABCMeta

        @classmethod
        def __subclasshook__(cls, C):
            if cls is PudbCollection:
                return all([
                    any("__contains__" in B.__dict__ for B in C.__mro__),
                    any("__iter__" in B.__dict__ for B in C.__mro__),
                ])
            return NotImplemented

    class PudbSequence:
        __metaclass__ = ABCMeta

        @classmethod
        def __subclasshook__(cls, C):
            if cls is PudbSequence:
                return all([
                    any("__getitem__" in B.__dict__ for B in C.__mro__),
                    any("__iter__" in B.__dict__ for B in C.__mro__),
                ])
            return NotImplemented

    class PudbMapping:
        __metaclass__ = ABCMeta

        @classmethod
        def __subclasshook__(cls, C):
            if cls is PudbMapping:
                return all([
                    any("__getitem__" in B.__dict__ for B in C.__mro__),
                    any("__iter__" in B.__dict__ for B in C.__mro__),
                    any("keys" in B.__dict__ for B in C.__mro__),
                ])
            return NotImplemented
    # }}}

try:
    import builtins
    from configparser import ConfigParser
except ImportError:
    import __builtin__ as builtins  # noqa: F401
    from ConfigParser import ConfigParser  # noqa: F401
