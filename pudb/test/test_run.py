import os

import pytest

from pudb import runscript
from pudb.debugger import Debugger
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
    assert ex.value.code == 0

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
    assert ex.value.code == 2

    captured = capsys.readouterr()

    assert "error: unrecognized arguments: -v" in captured.err
    assert not captured.out


@pytest.fixture
def light_debugger(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PUDB_TTY", raising=False)
    monkeypatch.setattr(Debugger, "_current_debugger", [])

    def init_debugger(self: Debugger, **_kwargs: object) -> None:
        self._tty_file = None  # pyright: ignore[reportPrivateUsage]
        self._current_debugger.append(self)  # pyright: ignore[reportPrivateUsage]

    monkeypatch.setattr(Debugger, "__init__", init_debugger)


@pytest.mark.usefixtures("light_debugger")
def test_runscript_releases_debugger(monkeypatch: pytest.MonkeyPatch) -> None:
    used: list[Debugger] = []

    def fake_runscript(_mainpyfile: str, dbg: Debugger, **_kwargs: object) -> None:
        used.append(dbg)

    monkeypatch.setattr("pudb._runscript", fake_runscript)

    runscript("dont_look_at_me.py")
    assert not Debugger._current_debugger  # pyright: ignore[reportPrivateUsage]

    runscript("dont_look_at_me.py")
    assert used[0] is not used[1]
