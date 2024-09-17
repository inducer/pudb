#!/usr/bin/env python3

import os

import pytest

from pudb.run import main


def csv(x):
    return "('" + "', '".join(x) + "',)"


main_version_scenarios = [
    ("-v",),
    ("--version",),
    ("--version", "dont_look_at_me.py"),
]


@pytest.mark.parametrize(
    "argv",
    [pytest.param(s, id=csv(s)) for s in main_version_scenarios],
)
def test_main_version(capsys, mocker, argv):
    mocker.patch("sys.argv", [os.path.basename(main.__code__.co_filename), *argv])

    with pytest.raises(SystemExit) as ex:
        main()
        assert ex.value == 0

    captured = capsys.readouterr()

    assert "pudb v" in captured.out


def test_main_v_with_args(capsys, mocker):
    """
    This will fail, because args is not only ``-v``,
    and that's reserved for future use ...
    """
    mocker.patch("sys.argv", [
        os.path.basename(main.__code__.co_filename),
        "-v",
        "dont_look_at_me.py"
    ])

    with pytest.raises(SystemExit) as ex:
        main()
        assert ex.value == 2

    captured = capsys.readouterr()

    assert "error: unrecognized arguments: -v" in captured.err
    assert not captured.out
