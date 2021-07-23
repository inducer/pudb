from pudb.ui_tools import Caption, CaptionParts
import pytest
import urwid


@pytest.fixture
def text_markups():
    from collections import namedtuple
    Markups = namedtuple("Markups",
            ["pudb_version", "hotkey", "full_source_filename",
                "alert", "default_separator", "custom_separator"])

    pudb_version = (None, "PuDB VERSION")
    hotkey = (None, "?:help")
    full_source_filename = (None, "/home/foo - bar/baz.py")
    alert = ("warning", "[POST-MORTEM MODE]")
    default_separator = (None, " - ")
    custom_separator = (None, " | ")
    return Markups(pudb_version, hotkey, full_source_filename,
            alert, default_separator, custom_separator)


@pytest.fixture
def captions(text_markups):
    empty = CaptionParts(*[(None, "")]*4)
    always_display = [
            text_markups.pudb_version, text_markups.hotkey,
            text_markups.full_source_filename]
    return {"empty": Caption(empty),
            "without_alert": Caption(CaptionParts(*always_display, (None, ""))),
            "with_alert": Caption(CaptionParts(*always_display, text_markups.alert)),
            "custom_separator": Caption(CaptionParts(*always_display, (None, "")),
                separator=text_markups.custom_separator),
            }


def test_init(captions):
    for key in ["empty", "without_alert", "with_alert"]:
        assert captions[key].separator == (None, " - ")
    assert captions["custom_separator"].separator == (None, " | ")


def test_str(captions):
    assert str(captions["empty"]) == ""
    assert str(captions["without_alert"]
               ) == "PuDB VERSION - ?:help - /home/foo - bar/baz.py"
    assert str(captions["with_alert"]
               ) == "PuDB VERSION - ?:help - /home/foo - bar/baz.py - [POST-MORTEM MODE]"  # noqa
    assert str(captions["custom_separator"]
               ) == "PuDB VERSION | ?:help | /home/foo - bar/baz.py"


def test_markup(captions):
    assert captions["empty"].markup \
        == [(None, ""), (None, " - "),
            (None, ""), (None, " - "),
            (None, "")]

    assert captions["without_alert"].markup \
        == [(None, "PuDB VERSION"), (None, " - "),
            (None, "?:help"), (None, " - "),
            (None, "/home/foo - bar/baz.py")]

    assert captions["with_alert"].markup \
        == [(None, "PuDB VERSION"), (None, " - "),
            (None, "?:help"), (None, " - "),
            (None, "/home/foo - bar/baz.py"), (None, " - "),
            ("warning", "[POST-MORTEM MODE]")]

    assert captions["custom_separator"].markup \
        == [(None, "PuDB VERSION"), (None, " | "),
            (None, "?:help"), (None, " | "),
            (None, "/home/foo - bar/baz.py")]


def test_render(captions):
    for k in captions.keys():
        sizes = {"wider_than_caption": (max(1, len(str(captions[k])) + 1), ),
                "equals_caption": (max(1, len(str(captions[k]))), ),
                "narrower_than_caption": (max(1, len(str(captions[k])) - 10), ),
                 }
        for s in sizes:
            got = captions[k].render(sizes[s])
            markup = captions[k]._get_fit_width_markup(sizes[s])
            expected = urwid.Text(markup).render(sizes[s])
            assert list(expected.content()) == list(got.content())


def test_set_text(captions):
    assert captions["empty"].caption_parts == CaptionParts(*[(None, "")]*4)
    for key in ["without_alert", "custom_separator"]:
        assert captions[key].caption_parts \
            == CaptionParts(
                    (None, "PuDB VERSION"),
                    (None, "?:help"),
                    (None, "/home/foo - bar/baz.py"),
                    (None, ""))
    assert captions["with_alert"].caption_parts \
            == CaptionParts(
                    (None, "PuDB VERSION"),
                    (None, "?:help"),
                    (None, "/home/foo - bar/baz.py"),
                    ("warning", "[POST-MORTEM MODE]"))


def test_rows(captions):
    for caption in captions.values():
        assert caption.rows(size=(99999, 99999)) == 1
        assert caption.rows(size=(80, 24)) == 1
        assert caption.rows(size=(1, 1)) == 1


def test_get_fit_width_markup(captions):
    # No need to check empty caption because
    # len(str(caption)) == 0 always smaller than min terminal column == 1

    # Set up
    caption = captions["with_alert"]
    caption_length = len(str(caption))
    full_source_filename = caption.caption_parts.full_source_filename[1]
    cut_only_filename = (
        max(1, caption_length - len(full_source_filename) + 5), )
    cut_more_than_filename = (max(1, caption_length
            - len(full_source_filename) - len("PuDB VE")), )
    sizes = {"equals_caption": (max(1, caption_length), ),
            "cut_only_filename": cut_only_filename,
            "cut_more_than_filename": cut_more_than_filename,
            "one_col": (1, ),
             }
    # Test
    assert caption._get_fit_width_markup(sizes["equals_caption"]) \
            == [(None, "PuDB VERSION"), (None, " - "),
                (None, "?:help"), (None, " - "),
                (None, "/home/foo - bar/baz.py"), (None, " - "),
                ("warning", "[POST-MORTEM MODE]")]
    assert caption._get_fit_width_markup(sizes["cut_only_filename"]) \
            == [(None, "PuDB VERSION"), (None, " - "),
                (None, "?:help"), (None, " - "),
                (None, "az.py"), (None, " - "), ("warning", "[POST-MORTEM MODE]")]
    assert caption._get_fit_width_markup(sizes["cut_more_than_filename"]) \
            == [(None, "RSION"), (None, " - "),
                (None, "?:help"), (None, " - "),
                (None, ""), (None, " - "), ("warning", "[POST-MORTEM MODE]")]
    assert caption._get_fit_width_markup(sizes["one_col"]) \
            == [(None, "")]*6 + [("warning", "]")]


def test_get_shortened_source_filename(captions):
    # No need to check empty caption because
    # len(str(caption)) == 0 always smaller than min terminal column == 1
    for k in ["with_alert", "without_alert", "custom_separator"]:
        caption_length = len(str(captions[k]))
        sizes = {"cut_at_path_sep": (max(1, caption_length - 1), ),
                "lose_some_dir": (max(1, caption_length - 2), ),
                "lose_all_dir": (max(1,
                    caption_length - len("/home/foo - bar/")), ),
                "lose_some_filename_chars": (max(1,
                    caption_length - len("/home/foo - bar/ba")), ),
                "lose_all": (max(1,
                    caption_length - len("/home/foo - bar/baz.py")), ),
                 }
        assert captions[k]._get_shortened_source_filename(sizes["cut_at_path_sep"]) \
                == "home/foo - bar/baz.py"
        assert captions[k]._get_shortened_source_filename(sizes["lose_some_dir"]) \
                == "foo - bar/baz.py"
        assert captions[k]._get_shortened_source_filename(sizes["lose_all_dir"]) \
                == "baz.py"
        assert captions[k]._get_shortened_source_filename(
                sizes["lose_some_filename_chars"]) \
                == "z.py"
        assert captions[k]._get_shortened_source_filename(sizes["lose_all"]) \
                == ""
