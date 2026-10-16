from __future__ import annotations


__copyright__ = """
Copyright (C) 2026 University of Illinois Board of Trustees
Copyright (C) 2026 'mayuriphad' (via https://github.com/inducer/pudb/pull/761)
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


from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

import pytest
from urwid import RadioButton


if TYPE_CHECKING:
    from collections.abc import Sequence

    from urwid import ListBox, SimpleListWalker, Widget

    from pudb.settings import ConfDict


@pytest.fixture
def conf_dict(monkeypatch: pytest.MonkeyPatch) -> ConfDict:
    from pudb import settings

    def save_config(_conf_dict: ConfDict) -> None:
        pass

    monkeypatch.setattr(settings, "save_config", save_config)
    monkeypatch.setattr(settings, "_config_", [None])
    monkeypatch.setattr(settings, "XDG_CONFIG_DIRS", [])
    return settings.load_config()


@pytest.mark.parametrize("shell", ["classic", "ptipython"])
def test_edit_config_saves_selected_shell(conf_dict: ConfDict, shell: str) -> None:
    """Accepting the settings dialog with a named shell selected must not
    raise and must store that shell."""
    from pudb.settings import edit_config

    def accept(
        lb: ListBox[int],
        _buttons: Sequence[tuple[str, object] | None],
        **_kwargs: object,
    ) -> bool:
        for widget in cast("SimpleListWalker[Widget]", lb.body):
            base_widget = widget.base_widget
            if (isinstance(base_widget, RadioButton)
                    and base_widget.get_label() == shell):
                base_widget.set_state(True)
        return True

    ui = MagicMock(dialog=MagicMock(side_effect=accept))

    edit_config(ui, conf_dict)

    assert conf_dict["shell"] == shell
