import pytest  # noqa: F401

from pudb.debugger import (
        NullSourceCodeProvider, FileSourceCodeProvider, DirectSourceCodeProvider)
from pudb.source_view import SourceLine


class TestNullSourceCodeProvider:
    def test_get_lines(self, mocker):
        provider = NullSourceCodeProvider()
        result = provider.get_lines(mocker.Mock())
        assert len(result) == 10
        assert isinstance(result[0], SourceLine)


class TestFileSourceCodeProvider:
    def test_string_file_name(self, mocker):
        mock_debugger = mocker.Mock()
        mock_debugger.canonic = mocker.Mock(return_value='<string>')
        provider = FileSourceCodeProvider(mock_debugger, 'test file name')
        result = provider.get_lines(mocker.MagicMock())
        assert len(result) == 1
        assert isinstance(result[0], SourceLine)

    def test_get_lines(self, mocker):
        provider = FileSourceCodeProvider(mocker.Mock(), 'test file name')
        result = provider.get_lines(mocker.MagicMock())
        assert len(result) == 1
        assert isinstance(result[0], SourceLine)


class TestDirectSourceCodeProvider:
    def test_get_lines(self, mocker):
        provider = DirectSourceCodeProvider(mocker.Mock(), 'test code')
        result = provider.get_lines(mocker.Mock())
        assert len(result) == 1
        assert isinstance(result[0], SourceLine)
