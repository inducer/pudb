from __future__ import annotations

import bdb
import sys
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from pudb.debugger import Debugger


if TYPE_CHECKING:
    from types import FrameType

    from pudb.debugger import OptExcInfo


def _make_debugger(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> Debugger:
    monkeypatch.setattr("pudb.debugger.get_save_config_path", lambda: str(tmp_path))
    monkeypatch.setattr("pudb.settings.load_breakpoints", list)
    monkeypatch.setattr(Debugger, "_current_debugger", [])
    return Debugger(stdin=StringIO(), stdout=StringIO(), term_size=(80, 24))


def test_step_next_exception_keeps_caller_frame(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    dbg = _make_debugger(monkeypatch, tmp_path)
    interactions: list[tuple[str, list[str], int, OptExcInfo | None]] = []

    def fake_call_with_ui(
        _func: object,
        exc_tuple: OptExcInfo | None = None,
        show_exc_dialog: bool = True,
    ) -> None:
        _ = show_exc_dialog
        stack_names = [frame.f_code.co_name for frame, _lineno in dbg.stack]
        interactions.append(
            (dbg.curframe.f_code.co_name, stack_names, dbg.curindex, exc_tuple)
        )
        if exc_tuple is None:
            dbg.set_next(dbg.curframe)
        else:
            dbg.set_quit()

    monkeypatch.setattr(dbg.ui, "call_with_ui", fake_call_with_ui)

    def failing() -> None:
        raise ValueError("boom")

    def caller() -> None:
        dbg.set_trace(paused=True)
        failing()

    try:
        with pytest.raises(bdb.BdbQuit):
            caller()
    finally:
        sys.settrace(None)
        dbg.close()

    assert len(interactions) == 2

    step_cur, step_stack, _, step_exc = interactions[0]
    assert step_cur == "caller"
    assert step_exc is None
    assert "test_step_next_exception_keeps_caller_frame" in step_stack

    exc_cur, exc_stack, exc_idx, exc_tuple = interactions[1]
    assert exc_tuple is not None
    assert exc_tuple[0] is ValueError
    assert exc_cur == "caller"
    assert exc_stack[exc_idx] == "caller"
    assert exc_stack[-2:] == ["caller", "failing"]
    assert "test_step_next_exception_keeps_caller_frame" in exc_stack


def test_post_mortem_avoids_duplicate_stack_frames(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    dbg = _make_debugger(monkeypatch, tmp_path)

    def noop(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(dbg.ui, "call_with_ui", noop)

    def inner() -> None:
        raise RuntimeError("inner boom")

    def outer() -> None:
        inner()

    exc_info: OptExcInfo | None = None
    outer_frame: FrameType | None = None
    try:
        outer()
    except RuntimeError:
        exc_info = sys.exc_info()
        assert exc_info[2] is not None
        outer_frame = exc_info[2].tb_next.tb_frame if exc_info[2].tb_next else None

    assert exc_info is not None
    assert outer_frame is not None

    try:
        dbg.enter_post_mortem(exc_info)  # pyright: ignore[reportUnknownMemberType]
        dbg.interaction(outer_frame, exc_info)

        stack_names = [frame.f_code.co_name for frame, _lineno in dbg.stack]
        assert stack_names == [
            "test_post_mortem_avoids_duplicate_stack_frames",
            "outer",
            "inner",
        ]
        assert dbg.curindex == len(dbg.stack) - 1
        assert dbg.curframe.f_code.co_name == "inner"
    finally:
        dbg.close()


def test_get_shortened_stack_trims_above_bottom_frame_with_tb(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    dbg = _make_debugger(monkeypatch, tmp_path)

    def inner() -> None:
        raise ZeroDivisionError("zero")

    def caller() -> None:
        inner()

    exc_info: OptExcInfo | None = None
    try:
        caller()
    except ZeroDivisionError:
        exc_info = sys.exc_info()

    assert exc_info is not None
    tb = exc_info[2]
    assert tb is not None
    caller_tb = tb.tb_next
    assert caller_tb is not None

    try:
        dbg.botframe = tb.tb_frame
        dbg.bottom_frame = caller_tb.tb_frame
        stack, index = dbg.get_shortened_stack(  # pyright: ignore[reportUnknownMemberType]
            caller_tb.tb_frame, caller_tb
        )
        stack_names = [frame.f_code.co_name for frame, _lineno in stack]
        assert stack_names == ["caller", "inner"]
        assert index == 0
    finally:
        dbg.close()
