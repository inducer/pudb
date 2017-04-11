# -*- coding: utf-8 -*-
from pudb.lowlevel import detect_encoding, decode_lines
from pudb.py3compat import PY3


def test_detect_encoding_nocookie():
    lines = ['Test Проверка']
    encoding, _ = detect_encoding(lines)
    assert encoding == 'utf-8'


def test_detect_encoding_cookie():
    lines = [
        '# coding=utf-8',
        'Test',
        'Проверка'
    ]
    encoding, _ = detect_encoding(lines)
    assert encoding == 'utf-8'


def test_decode_lines():
    lines = [
        '# coding=utf-8',
        'Test',
        'Проверка',
    ]
    if PY3:
        assert lines == list(decode_lines(lines))
    else:
        assert [l.decode('utf-8') for l in lines] == list(decode_lines(lines))
