import pytest
import sys

from io import StringIO

import spy.fragments


def test_init():
    stream = StringIO('these are\nsome lines')
    f = spy.fragments.init(stream)([])
    assert list(next(f)) == ['these are', 'some lines']


def test_many():
    input_ = [['foo', 'bar', 'baz']]

    f = spy.fragments.many(input_)
    assert list(f) == ['foo', 'bar', 'baz']

    f = spy.fragments.many(spy.fragments.many(input_))
    assert list(f) == list('foobarbaz')


class TestPrint:
    def test_iterable(self, capsys):
        f = spy.fragments.print([(x for x in [1, 2, 3, 4, 5, 6])])
        list(f)
        assert capsys.readouterr()[0] == '<iterable [1, 2, 3, 4, 5, ...]>\n'

    def test_list(self, capsys):
        f = spy.fragments.print([[1, 2, 3]])
        list(f)
        assert capsys.readouterr()[0] == '[1, 2, 3]\n'

    def test_str(self, capsys):
        f = spy.fragments.print(['this is a test'])
        list(f)
        assert capsys.readouterr()[0] == 'this is a test\n'


class TestLimit:
    def test_dots(self):
        f = spy.fragments.make_limit(end=0)([])
        assert list(f) == []
        f = spy.fragments.make_limit(end=0)(['foo'])
        assert list(f) == []

    def test_start(self):
        f = spy.fragments.make_limit(start=2)(['foo', 'bar', 'baz'])
        assert list(f) == ['baz']

    def test_stops_iterating(self):
        ita = iter(['foo', 'bar', 'baz'])
        f = spy.fragments.make_limit(end=1)(ita)
        assert list(f) == ['foo']
        assert list(ita) == ['bar', 'baz']
