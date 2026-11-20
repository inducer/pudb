from io import StringIO
from unittest.mock import Mock

from pudb.debugger import CONFIG, Debugger, DebuggerUI
from pudb.source_view import SourceLine


def test_hidden_cmdline_does_not_take_focus(monkeypatch, tmp_path):
    monkeypatch.setitem(CONFIG, "hide_cmdline_win", True)
    monkeypatch.setitem(CONFIG, "hotkeys_toggle_cmdline_focus", "ctrl x")
    monkeypatch.setattr("pudb.debugger.get_save_config_path", lambda: str(tmp_path))
    size = (80, 24)
    ui = DebuggerUI(Mock(spec=Debugger), StringIO(), StringIO(), size)
    ui.source[:] = [SourceLine(ui, "pass")]

    ui.top.keypress(size, "down")
    assert ui.lhs_col.focus is ui.source_attr

    ui.top.keypress(size, "ctrl x")
    assert ui.lhs_col.focus is ui.cmdline_sigwrap
    assert ui.cmdline_on

    ui.top.keypress(size, "ctrl x")
    ui.top.keypress(size, "down")
    assert ui.lhs_col.focus is ui.source_attr
    assert not ui.cmdline_on
