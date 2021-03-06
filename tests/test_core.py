import pytest
import sys

from io import StringIO

import spy


@spy.fragment
def noop(v):
    return v


@spy.fragment
def upper(v):
    return v.upper()


@spy.fragment
def reverse(v):
    return v[::-1]


@spy.fragment
def drop_foo(v):
    if v.lower() == 'foo':
        return spy.DROP
    return v


@spy.fragment
def many(v):
    return spy.many(v)


@spy.fragment
def collect(v, context):
    return spy.collect(context)


def test_chain():
    seq = [noop, upper, noop, reverse, noop]
    chain = spy.chain(seq)
    assert list(chain.apply(['FOO', 'BAR'])) == ['OOF', 'RAB']

    output = []
    @spy.fragment
    def capture(v):
        output.append(v)
    seq.append(capture)

    chain = spy.chain(seq)
    chain.run_to_exhaustion(['FOO', 'BAR'])
    assert output == ['OOF', 'RAB']


def test_auto_fragments():
    @spy.fragment
    def already_a_fragment(v):
        v[0] = 'x'
        return v

    def not_a_fragment(v):
        v[1] = 'y'
        return v

    chain = spy.chain.auto_fragments([already_a_fragment, not_a_fragment])
    assert next(chain([['a', 'a']])) == ['x', 'y']


def test_index_offset():
    with pytest.raises(TypeError):
        c = spy.chain([noop], 'fubar')


def test_format():
    seq = [noop, upper, 'spaghetti']
    chain = spy.chain(seq, index_offset=-1)
    lines = chain.format().splitlines()
    assert lines[0].strip().startswith('|')
    assert 'test_core.noop' in lines[0]
    assert lines[1].strip().startswith('1 |')
    assert 'test_core.upper' in lines[1]
    assert 'UNKNOWN' in lines[2]


def test_defaults(capsys):
    chain = spy.chain.with_defaults([many])
    chain.run_to_exhaustion([['some', 'test', 'data']])
    out, err = capsys.readouterr()
    assert out == 'some\ntest\ndata\n'


def test_many():
    seq = [many, upper]
    chain = spy.chain(seq)
    assert list(chain.apply(['foo', 'bar'])) == list('FOOBAR')


def test_collect():
    seq = [collect]
    chain = spy.chain(seq)
    assert list(next(chain.apply(['foo', 'bar']))) == ['foo', 'bar']


def test_collect_nocontext():
    with pytest.raises(ValueError):
        spy.collect(None)


def test_drop():
    seq = [drop_foo]
    chain = spy.chain(seq)
    for item in chain.apply(['foo', 'bar', 'foo', 'test']):
        assert item.lower() != 'foo'
