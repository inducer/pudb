from pudb.ui_tools import make_canvas

class TestMakeCanvas():
    def test_simple(self):
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

    def test_multiple(self):
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

    def test_boundary(self):
        text = u'aaaaaa'
        canvas = make_canvas(
            txt=[text],
            attr=[[('var value', len(text))]],
            maxcol=len(text)
        )
        assert list(canvas.content()) == [[('var value', None, b'aaaaaa')]]

    def test_byte_boundary(self):
        text = u'aaaaaaé'
        canvas = make_canvas(
            txt=[text],
            attr=[[('var value', len(text))]],
            maxcol=len(text)
        )
        assert list(canvas.content()) == [[('var value', None, b'aaaaaa\xc3\xa9')]]
