import spy.fragments

import pytest

def test_many():
    input_ = [['foo', 'bar', 'baz']]

    f = spy.fragments.many(input_)
    assert list(f) == ['foo', 'bar', 'baz']

    f = spy.fragments.many(spy.fragments.many(input_))
    assert list(f) == list('foobarbaz')


class TestLimit:
    def test_dots(self):
        f = spy.fragments.make_limit(end=0)([])
        assert list(f) == []
        f = spy.fragments.make_limit(end=0)(['foo'])
        assert list(f) == ['...']

    def test_start(self):
        f = spy.fragments.make_limit(start=2)(['foo', 'bar', 'baz'])
        assert list(f) == ['baz']

    def test_stops_iterating(self):
        ita = iter(['foo', 'bar', 'baz'])
        f = spy.fragments.make_limit(end=1)(ita)
        assert list(f) == ['foo', '...']
        assert list(ita) == ['baz']
