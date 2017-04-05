# - encoding: utf-8 -

from pudb.ui_tools import make_canvas


def test_simple():
    text = u'aaaaaa'
    canvas = make_canvas(
        txt=[text],
        attr=[[('var value', len(text))]],
        maxcol=len(text) + 5
    )
    content = list(canvas.content())
    assert content == [
        [('var value', None, b'aaaaaa'), (None, None, b' ' * 5)]
    ]


def test_multiple():
    canvas = make_canvas(
        txt=[u'Return: None'],
        attr=[[('return label', 8), ('return value', 4)]],
        maxcol=100
    )
    content = list(canvas.content())
    assert content == [
        [('return label', None, b'Return: '),
         ('return value', None, b'None'),
         (None, None, b' ' * 88)]
    ]


def test_boundary():
    text = u'aaaaaa'
    canvas = make_canvas(
        txt=[text],
        attr=[[('var value', len(text))]],
        maxcol=len(text)
    )
    assert list(canvas.content()) == [[('var value', None, b'aaaaaa')]]


def test_byte_boundary():
    text = u'aaaaaaé'
    canvas = make_canvas(
        txt=[text],
        attr=[[('var value', len(text))]],
        maxcol=len(text)
    )
    assert list(canvas.content()) == [[('var value', None, b'aaaaaa\xc3\xa9')]]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
