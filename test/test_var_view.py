# -*- coding: utf-8 -*-
import contextlib
import itertools
import string
import unittest

from pudb.py3compat import (
    text_type, integer_types, string_types,
    PudbCollection, PudbMapping, PudbSequence,
)
from pudb.var_view import FrameVarInfo, BasicValueWalker, ui_log


class A:
    pass


class A2(object):
    pass


def test_get_stringifier():
    from pudb.var_view import InspectInfo, get_stringifier

    try:
        import numpy as np
    except ImportError:
        numpy_values = []
    else:
        numpy_values = [np.float32(5), np.zeros(5)]

    for value in [
            A, A2, A(), A2(), u"lól".encode("utf8"), u"lól",
            1233123, [u"lól".encode("utf8"), u"lól"],
            ] + numpy_values:
        for display_type in ["type", "repr", "str"]:
            iinfo = InspectInfo()
            iinfo.display_type = display_type

            strifier = get_stringifier(iinfo)

            s = strifier(value)
            assert isinstance(s, text_type)


class FrameVarInfoForTesting(FrameVarInfo):
    def get_inspect_info(self, id_path, read_only):
        iinfo = super(FrameVarInfoForTesting, self).get_inspect_info(
            id_path, read_only)
        iinfo.access_level = "private"
        iinfo.display_type = "repr"
        iinfo.show_detail = True
        iinfo.show_methods = True
        return iinfo


class Reasonable(object):
    def __init__(self):
        self.x = 42

    def bar(self):
        return True

    @property
    def red(self):
        return "red"

    @classmethod
    def blue(cls):
        return "blue"

    @staticmethod
    def green():
        return "green"

    def _private(self):
        return "shh"

    def __magicsomething__(self):
        return "amazing"


class SetWithOverridenBool(set):
    def __init__(self, iterable, truthy=True):
        super(SetWithOverridenBool, self).__init__(iterable)
        self.truthy = truthy

    def __bool__(self):
        return self.truthy


def method_factory(method_name):
    def method(self, *args, **kwargs):
        func = getattr(self.__internal_dict__, method_name)
        try:
            return func(*args, **kwargs)
        except KeyError:
            # Classes without __iter__ are expected to raise IndexError in this
            # sort of case. Frustrating, I know.
            if (method_name == "__getitem__"
                    and args and isinstance(args[0], integer_types)):
                raise IndexError
            raise
    return method


def containerlike_class_generator():
    methods = set([
        "__contains__",
        "__getitem__",
        "__iter__",
        "__len__",
        "__reversed__",
        "count",
        "get",
        "index",
        "items",
        "keys",
        "values",
    ])

    # Deliberately starting from 0
    for r in range(0, len(methods) + 1):
        for selected_methods in sorted(
                map(sorted, itertools.combinations(methods, r))):

            class ContainerlikeClass(object):
                def __init__(self, iterable):
                    self.__internal_dict__ = dict(iterable)

                @classmethod
                def name(cls):
                    return "ContainerlikeClass:{}".format(
                        ":".join(selected_methods))

            # for method in always_define.union(selected_methods):
            for method in selected_methods:
                func = method_factory(method)
                setattr(ContainerlikeClass, method, func)

            yield ContainerlikeClass


class BaseValueWalkerTestCase(unittest.TestCase):
    BASIC_TYPES = []
    BASIC_TYPES.append(type(None))
    BASIC_TYPES.extend(integer_types)
    BASIC_TYPES.extend(string_types)
    BASIC_TYPES.extend((float, complex))
    BASIC_TYPES = tuple(BASIC_TYPES)

    def value_string(self, obj):
        if isinstance(obj, self.BASIC_TYPES):
            return repr(obj)
        return repr(obj) + self.mod_str

    @contextlib.contextmanager
    def patched_logging(self):
        def fake_exception_log(*args, **kwargs):
            self.fail("ui_log.exception was unexpectedly called")

        old_logger = ui_log.exception
        ui_log.exception = fake_exception_log
        try:
            yield
        finally:
            ui_log.exception = old_logger

    def walked_values(self):
        return [(w.var_label, w.value_str)
                for w in self.walker.widget_list]

    def attrs(self, obj):
        return [_label for _label in sorted(dir(obj))
                if not _label.startswith("__")]

    def find_expected_attrs(self, obj):
        """
        Recursively `dir()` the object and return (label, value string) pairs
        for each attribute that doesn't start with "__". Should match the
        order that these attributes would appear in the var_view.
        """
        found = []
        for _label in self.attrs(obj):
            found.append(("." + str(_label),
                          self.value_string(getattr(obj, _label))))
            found.extend(self.find_expected_attrs(getattr(obj, _label)))
        return found

    @classmethod
    def setUpClass(cls):
        cls.mod_str = " [pri+()]"


class ValueWalkerTest(BaseValueWalkerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod_str = " [pri+()]"

    def setUp(self):
        self.walker = BasicValueWalker(FrameVarInfoForTesting())

    def walked_values(self):
        return [(w.var_label, w.value_str)
                for w in self.walker.widget_list]

    def test_simple_values(self):
        values = [
            # numbers
            0,
            1,
            -1234567890412345243,
            float(4.2),
            float("inf"),
            complex(1.3, -1),

            # strings
            "",
            "a",
            "foo bar",
            "  lots\tof\nspaces\r ",
            "♫",

            # other
            False,
            True,
            None,
        ]
        for label, value in enumerate(values):
            with self.patched_logging():
                self.walker.walk_value(parent=None, label=label, value=value)

        expected = [(_label, repr(x)) for _label, x in enumerate(values)]
        received = self.walked_values()
        self.assertListEqual(expected, received)

    def test_set(self):
        label = "xs"
        value = set([42, "foo", None, False])
        with self.patched_logging():
            self.walker.walk_value(parent=None, label=label, value=value)

        expected = {(None, repr(x)) for x in value}
        expected.add((label, repr(value) + self.mod_str))
        received = set(self.walked_values())
        self.assertSetEqual(expected, received)

    def test_frozenset(self):
        label = "xs"
        value = frozenset([42, "foo", None, False])
        with self.patched_logging():
            self.walker.walk_value(parent=None, label=label, value=value)

        expected = {(None, repr(x)) for x in value}
        expected.add((label, repr(value) + self.mod_str))
        received = frozenset(self.walked_values())
        self.assertSetEqual(expected, received)

    def test_dict(self):
        label = "xs"
        value = {
            0:                   42,
            "a":                 "foo",
            "":                  None,
            True:                False,
            frozenset(range(3)): "abc",
        }
        with self.patched_logging():
            self.walker.walk_value(parent=None, label=label, value=value)

        expected = set((repr(k), repr(v)) for k, v in value.items())
        expected.add((label, repr(value) + self.mod_str))
        received = set(self.walked_values())
        self.assertSetEqual(expected, received)

    def test_list(self):
        label = "xs"
        value = [42, "foo", None, False]
        with self.patched_logging():
            self.walker.walk_value(parent=None, label=label, value=value)

        expected = [(label, repr(value) + self.mod_str)]
        expected.extend([(repr(_label), repr(x))
                         for _label, x in enumerate(value)])
        received = self.walked_values()
        self.assertListEqual(expected, received)

    def test_containerlike_classes(self):
        for containerlike_class in containerlike_class_generator():
            label = containerlike_class.name()
            value = containerlike_class(zip(string.ascii_lowercase, range(7)))
            self.walker = BasicValueWalker(FrameVarInfoForTesting())

            with self.patched_logging():
                self.walker.walk_value(parent=None, label=label, value=value)

            if isinstance(value, PudbMapping):
                expected = {(label, repr(value) + self.mod_str)}
                expected.update([(repr(_label), repr(value[_label]))
                                 for _label in value])
                received = set(self.walked_values())
                self.assertSetEqual(expected, received)
            elif isinstance(value, PudbSequence):
                expected = [(label, repr(value) + self.mod_str)]
                expected.extend([(repr(index), repr(entry))
                                 for index, entry in enumerate(value)])
                received = self.walked_values()
                self.assertListEqual(expected, received)
            elif isinstance(value, PudbCollection):
                expected = [(label, repr(value) + self.mod_str)]
                expected.extend([(None, repr(entry))
                                 for entry in value])
                received = self.walked_values()
                self.assertListEqual(expected, received)
            else:
                expected = [(label, repr(value) + self.mod_str)]
                expected.extend(self.find_expected_attrs(value))
                received = self.walked_values()
                self.assertListEqual(expected, received)


class ValueWalkerClassesTest(BaseValueWalkerTestCase):
    def test_reasonable_class(self):
        label = "Reasonable"
        value = Reasonable
        self.walker = BasicValueWalker(FrameVarInfoForTesting())

        with self.patched_logging():
            with self.patched_logging():
                self.walker.walk_value(parent=None, label=label, value=value)

        expected = [(label, repr(value) + self.mod_str)]
        expected.extend(self.find_expected_attrs(Reasonable))
        received = self.walked_values()
        self.assertListEqual(expected, received)

    def test_maybe_unreasonable_classes(self):
        for containerlike_class in containerlike_class_generator():
            label = containerlike_class.name()
            value = containerlike_class
            self.walker = BasicValueWalker(FrameVarInfoForTesting())

            with self.patched_logging():
                self.walker.walk_value(parent=None, label=label, value=value)

            expected = [(label, repr(value) + self.mod_str)]
            expected.extend(self.find_expected_attrs(containerlike_class))
            received = self.walked_values()
            self.assertListEqual(expected, received)
