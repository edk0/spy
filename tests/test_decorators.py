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


def test_many():
    @spy.fragment
    @decorators.many
    def test(v):
        return [1, 2, 3, 4, 5]

    l = spy.chain([test])
    assert list(l) == [1, 2, 3, 4, 5]


def test_once():
    calls = 0

    @spy.fragment
    @decorators.once
    def test(v):
        nonlocal calls
        calls += 1
        return 'a'

    spy.chain([test], ['x'] * 20).run_to_exhaustion()

    assert calls == 1
