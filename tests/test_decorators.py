import spy
from spy import decorators


def test_accumulate(capsys):
    calls = 0

    @spy.fragment
    @decorators.accumulate
    def test(v):
        nonlocal calls
        calls += 1
        return v

    try:
        spy.chain([test]).run_to_exhaustion(['x'])
    except KeyboardInterrupt:
        assert capsys.readouterr() == ''

    assert calls == 1


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

    l = spy.chain([test]).apply([None])
    assert list(l) == [1, 2, 3, 4, 5]


def test_format():
    @spy.fragment
    @decorators.format
    def test():
        return {'test': 1}, '{test}23'

    l = spy.chain([test]).apply([None])
    assert list(l) == ['123']


def test_regex():
    @spy.fragment
    @decorators.regex
    def test():
        return {}, '1(2)3'

    l = list(spy.chain([test]).apply(['123']))
    assert len(l) == 1
    assert l[0].group(1) == '2'
