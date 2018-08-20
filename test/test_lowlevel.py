# -*- coding: utf-8 -*-
from pudb.lowlevel import detect_encoding, decode_lines
from pudb.py3compat import PY3


def test_detect_encoding_nocookie():
    lines = [u'Test Проверка']
    lines = [l.encode('utf-8') for l in lines]
    encoding, _ = detect_encoding(iter(lines))
    assert encoding == 'utf-8'


def test_detect_encoding_cookie():
    lines = [
        u'# coding=utf-8',
        u'Test',
        u'Проверка'
    ]
    lines = [l.encode('utf-8') for l in lines]
    encoding, _ = detect_encoding(iter(lines))
    assert encoding == 'utf-8'


def test_decode_lines():
    unicode_lines = [
        u'# coding=utf-8',
        u'Test',
        u'Проверка',
    ]
    lines = [l.encode('utf-8') for l in unicode_lines]
    if PY3:
        assert unicode_lines == list(decode_lines(iter(lines)))
    else:
        assert [l.decode('utf-8') for l in lines] == list(decode_lines(iter(lines)))
