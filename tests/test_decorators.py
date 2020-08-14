import clize.errors
import lenses
import pytest

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
    def test(v):
        return {'test': 1}, '{test}23'

    l = spy.chain([test]).apply([None])
    assert list(l) == ['123']


def test_regex():
    @spy.fragment
    @decorators.regex
    def test(v):
        return {}, '1(2)3'

    l = list(spy.chain([test]).apply(['123']))
    assert len(l) == 1
    assert l[0].group(1) == '2'


def test_keywords():
    # keywords only works with base functions that have _spy_setenv, so pure
    # python API won't work
    with pytest.raises(ValueError):
        @spy.fragment
        @decorators.keywords
        def test(v):
            pass
    def build():
        env = {}
        def test(v):
            return env['a']
        def setenv(env_):
            nonlocal env
            env = env_
        test._spy_setenv = setenv
        return test
    test = spy.fragment(decorators.keywords(build()))
    l = list(spy.chain([test]).apply([{'a': 'xyz'}]))
    assert l[0] == 'xyz'


def test_convert_focus():
    assert decorators._convert_focus('_.Each()[2]') == lenses.lens.Each()[2]
    assert decorators._convert_focus('1::2') == lenses.lens[1::2]
    assert decorators._convert_focus('1:-1') == lenses.lens[1:-1]
    assert decorators._convert_focus('1:2:3:4') == '1:2:3:4'
    assert decorators._convert_focus('1:abc') == '1:abc'
    assert decorators._convert_focus('1') == 1
    assert decorators._convert_focus('.abc') == 'abc'


def test_convert_focus_without_lenses(monkeypatch):
    monkeypatch.setattr(decorators, 'lenses', None)
    assert decorators._convert_focus('_1') == '_1'
    assert decorators._convert_focus('1') == 1
    assert decorators._convert_focus('.abc') == 'abc'

    with pytest.raises(clize.errors.UserError):
        decorators._convert_focus('1::2')


def test_focus():
    @spy.fragment
    @decorators.focus(1)
    def test(v):
        return v * 3
    l = list(spy.chain([test]).apply([[1,2,3], [4,5,6]]))
    assert l == [[1,6,3], [4,15,6]]


def test_focus_without_lenses(monkeypatch):
    monkeypatch.setattr(decorators, 'lenses', None)
    test_focus()


def test_magnify():
    @spy.fragment
    @decorators.magnify(1)
    def test(v):
        return v * 3
    l = list(spy.chain([test]).apply([[1,2,3], [4,5,6]]))
    assert l == [6, 15]


def test_magnify_without_lenses(monkeypatch):
    monkeypatch.setattr(decorators, 'lenses', None)
    test_magnify()
