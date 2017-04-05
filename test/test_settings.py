import collections

import pytest  # noqa: F401

from pudb.py3compat import builtins
from pudb.settings import load_breakpoints, save_breakpoints


def test_load_breakpoints(mocker):
    fake_data = ['b /home/user/test.py:41'], ['b /home/user/test.py:50']
    mock_open = mocker.mock_open()
    mock_open.return_value.readlines.side_effect = fake_data
    mocker.patch.object(builtins, 'open', mock_open)
    mocker.patch('pudb.settings.lookup_module',
            mocker.Mock(return_value='/home/user/test.py'))
    mocker.patch('pudb.settings.get_breakpoint_invalid_reason',
            mocker.Mock(return_value=None))
    result = load_breakpoints()
    expected = [('/home/user/test.py', 41, False, None, None),
                ('/home/user/test.py', 50, False, None, None)]
    assert result == expected


def test_save_breakpoints(mocker):
    MockBP = collections.namedtuple('MockBreakpoint', 'file line cond')
    mock_breakpoints = [MockBP('/home/user/test.py', 41, None),
                        MockBP('/home/user/test.py', 50, None)]
    mocker.patch('pudb.settings.get_breakpoints_file_name',
                 mocker.Mock(return_value='saved-breakpoints'))
    mock_open = mocker.mock_open()
    mocker.patch.object(builtins, 'open', mock_open)

    save_breakpoints(mock_breakpoints)
    mock_open.assert_called_with('saved-breakpoints', 'w')
