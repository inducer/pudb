import contextlib
import itertools
import string
import unittest

from pudb.var_view import (
    BasicValueWalker,
    FrameVarInfo,
    InspectInfo,
    PudbCollection,
    PudbMapping,
    PudbSequence,
    STRINGIFIERS,
    ValueWalker,
    get_stringifier,
    ui_log,
)


class A:
    pass


class A2:
    pass


def test_get_stringifier():
    try:
        import numpy as np
    except ImportError:
        numpy_values = []
    else:
        numpy_values = [np.float32(5), np.zeros(5)]

    for value in [
            A, A2, A(), A2(), "lól".encode(), "lól",
            1233123, ["lól".encode(), "lól"],
            ] + numpy_values:
        for display_type in STRINGIFIERS:
            iinfo = InspectInfo()
            iinfo.display_type = display_type

            strifier = get_stringifier(iinfo)

            s = strifier(value)
            assert isinstance(s, str)


class FrameVarInfoForTesting(FrameVarInfo):
    def __init__(self, paths_to_expand=None):
        super().__init__()
        if paths_to_expand is None:
            paths_to_expand = set()
        self.paths_to_expand = paths_to_expand

    def get_inspect_info(self, id_path, read_only):
        iinfo = super().get_inspect_info(
            id_path, read_only)
        iinfo.access_level = "all"
        iinfo.display_type = "repr"
        iinfo.show_methods = True

        if id_path in self.paths_to_expand:
            iinfo.show_detail = True
        return iinfo


class Reasonable:
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


def method_factory(method_name):
    def method(self, *args, **kwargs):
        func = getattr(self.__internal_dict__, method_name)
        try:
            return func(*args, **kwargs)
        except KeyError:
            # Classes without __iter__ are expected to raise IndexError in this
            # sort of case. Frustrating, I know.
            if (method_name == "__getitem__"
                    and args and isinstance(args[0], int)):
                raise IndexError
            raise
    return method


def generate_containerlike_class():
    methods = {
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
    }

    # Deliberately starting from 0
    for r in range(0, len(methods) + 1):
        for selected_methods in sorted(
                map(sorted, itertools.combinations(methods, r))):

            class ContainerlikeClass:
                def __init__(self, iterable):
                    self.__internal_dict__ = dict(iterable)

                @classmethod
                def name(cls):
                    return "ContainerlikeClass:{}".format(
                        ":".join(selected_methods))

            for method in selected_methods:
                func = method_factory(method)
                setattr(ContainerlikeClass, method, func)

            yield ContainerlikeClass


class BaseValueWalkerTestCase(unittest.TestCase):
    """
    There are no actual tests defined in this class, it provides utitlities
    useful for testing the variable view in variaous ways.
    """
    EMPTY_ITEM = (ValueWalker.EMPTY_LABEL, None)
    MOD_STR = " [all+()]"

    def setUp(self):
        self.values_to_expand = []
        self.class_counts = {
            "mappings": 0,
            "sequences": 0,
            "collections": 0,
            "other": 0,
        }

    def value_string(self, obj, expand=True):
        if expand and obj in self.values_to_expand:
            return repr(obj) + self.MOD_STR
        return repr(obj)

    def walked_values(self):
        return [(w.var_label, w.value_str)
                for w in self.walker.widget_list]

    def expected_attrs(self, obj):
        """
        `dir()` the object and return (label, value string) pairs for each
        attribute. Should match the order that these attributes would appear in
        the var_view.
        """
        return [("." + str(label),
                 self.value_string(getattr(obj, label), expand=False))
                for label in sorted(dir(obj))]

    @contextlib.contextmanager
    def patched_logging(self):
        """
        Context manager that patches ui_log.exception such that the test will
        fail if it is called.
        """
        def fake_exception_log(*args, **kwargs):
            self.fail("ui_log.exception was unexpectedly called")

        old_logger = ui_log.exception
        ui_log.exception = fake_exception_log
        try:
            yield
        finally:
            ui_log.exception = old_logger

    def assert_walks_contents(self, container, label="xs"):
        expand_paths = {label}
        self.values_to_expand = [container]
        self.walker = BasicValueWalker(FrameVarInfoForTesting(expand_paths))

        # Build out list of extected view contents according to container type.
        expected = [(label, self.value_string(container))]
        if isinstance(container, PudbMapping):
            expected.extend([(f"[{repr(key)}]", repr(container[key]))
                             for key in container.keys()]
                            or [self.EMPTY_ITEM])
            self.class_counts["mappings"] += 1
        elif isinstance(container, PudbSequence):
            expected.extend([(f"[{repr(index)}]", repr(entry))
                             for index, entry in enumerate(container)]
                            or [self.EMPTY_ITEM])
            self.class_counts["sequences"] += 1
        elif isinstance(container, PudbCollection):
            expected.extend([("[]", repr(entry))
                             for entry in container]
                            or [self.EMPTY_ITEM])
            self.class_counts["collections"] += 1
        else:
            self.class_counts["other"] += 1
        expected.extend(self.expected_attrs(container))

        with self.patched_logging():
            self.walker.walk_value(parent=None, label=label, value=container)

        received = self.walked_values()
        self.assertListEqual(expected, received)

    def assert_class_counts_equal(self, seen=None):
        """
        This is kinda weird since at first it looks like its testing the test
        code, but really it's testing the `isinstance` checks. But it is also
        true that it tests the test code, kind of like a sanity check.
        """
        expected = {
            "mappings": 0,
            "sequences": 0,
            "collections": 0,
            "other": 0,
        }
        if seen is not None:
            expected.update(seen)
        self.assertDictEqual(expected, self.class_counts)


class ValueWalkerTest(BaseValueWalkerTestCase):
    def test_simple_values(self):
        self.walker = BasicValueWalker(FrameVarInfoForTesting())
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
                self.walker.walk_value(parent=None,
                                       label=str(label),
                                       value=value)

        expected = [(str(_label), repr(x)) for _label, x in enumerate(values)]
        received = self.walked_values()
        self.assertListEqual(expected, received)

    def test_simple_values_expandable(self):
        """
        Simple values like numbers and strings are now expandable so we can
        peak under the hood and take a look at their attributes. Make sure
        that's working properly.
        """
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
            # "  lots\tof\nspaces\r ",  # long, hits continuation item
            "♫",

            # other
            False,
            True,
            None,
        ]
        for value in values:
            self.assert_walks_contents(value)

    def test_set(self):
        self.assert_walks_contents({
            42, "foo", None, False, (), ("a", "tuple")
        })
        self.assert_class_counts_equal({"collections": 1})

    def test_frozenset(self):
        self.assert_walks_contents(frozenset([
            42, "foo", None, False, (), ("a", "tuple")
        ]))
        self.assert_class_counts_equal({"collections": 1})

    def test_dict(self):
        self.assert_walks_contents({
            0:                   42,
            "a":                 "foo",
            "":                  None,
            True:                False,
            frozenset(range(3)): "abc",
            ():                  "empty tuple",
            (1, 2, "c", ()):     "tuple",
        })
        self.assert_class_counts_equal({"mappings": 1})

    def test_list(self):
        self.assert_walks_contents([
            42, "foo", None, False, (), ("a", "tuple")
        ])
        self.assert_class_counts_equal({"sequences": 1})

    def test_tuple(self):
        self.assert_walks_contents((
            42, "foo", None, False, (), ("a", "tuple")
        ))
        self.assert_class_counts_equal({"sequences": 1})

    def test_containerlike_classes(self):
        class_count = 0
        for cls_idx, containerlike_class in enumerate(
                generate_containerlike_class()):
            label = containerlike_class.name()
            value = containerlike_class(zip(string.ascii_lowercase,
                                            range(3, 10)))
            self.assert_walks_contents(container=value, label=label)
            class_count = cls_idx + 1

        self.assert_class_counts_equal({
            "mappings": 256,
            "sequences": 256,
            "collections": 256,
            "other": 1280,
        })

        walked_total = (self.class_counts["mappings"]
                        + self.class_counts["sequences"]
                        + self.class_counts["collections"]
                        + self.class_counts["other"])

        # +1 here because enumerate starts from 0, not 1
        self.assertEqual(class_count, walked_total)

    def test_empty_frozenset(self):
        self.assert_walks_contents(frozenset())

    def test_empty_set(self):
        self.assert_walks_contents(set())

    def test_empty_dict(self):
        self.assert_walks_contents(dict())

    def test_empty_list(self):
        self.assert_walks_contents(list())

    def test_reasonable_class(self):
        """
        Are the class objects themselves expandable?
        """
        self.assert_walks_contents(Reasonable, label="Reasonable")
        self.assert_class_counts_equal({"other": 1})

    def test_maybe_unreasonable_classes(self):
        """
        Are class objects, that might look like containers if we're not
        careful, reasonably expandable?
        """
        for containerlike_class in generate_containerlike_class():
            self.assert_walks_contents(
                container=containerlike_class,
                label=containerlike_class.name()
            )

        # This effectively makes sure that class definitions aren't considered
        # containers.
        self.assert_class_counts_equal({"other": 2048})
