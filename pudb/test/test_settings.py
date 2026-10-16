from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def conf_dict(monkeypatch):
    from pudb import settings

    monkeypatch.setattr(settings, "save_config", lambda conf_dict: None)
    monkeypatch.setattr(settings, "_config_", [None])
    monkeypatch.setattr(settings, "XDG_CONFIG_DIRS", [])
    return settings.load_config()


@pytest.mark.parametrize("shell", ["classic", "ptipython"])
def test_edit_config_saves_selected_shell(conf_dict, shell):
    """Accepting the settings dialog with a named shell selected must not
    raise and must store that shell."""
    from pudb.settings import edit_config

    def accept(lb, buttons, title=None):
        for widget in lb.body:
            widget = getattr(widget, "original_widget", widget)
            if getattr(widget, "label", None) == shell:
                widget.set_state(True)
        return True

    ui = MagicMock()
    ui.dialog.side_effect = accept

    edit_config(ui, conf_dict)

    assert conf_dict["shell"] == shell
