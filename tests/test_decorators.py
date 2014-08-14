import spy
from spy import decorators


def test_callable():
    called = False
    def target(v):
        nonlocal called
        called = True

    @decorators.callable
    def test(v):
        return target

    test('hello')

    assert called


def test_filter():
    @decorators.filter
    def test(v):
        return v.lower() != 'foo'

    assert test('FOO') == spy.DROP
    assert test('BAR') == 'BAR'
