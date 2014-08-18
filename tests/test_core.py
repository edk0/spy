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
def collect(v):
    return spy.collect()


def test_chain():
    seq = [noop, upper, noop, reverse, noop]
    chain = spy.chain(seq, bootstrap=['foo', 'bar'])
    assert list(chain) == ['OOF', 'RAB']

    output = []
    @spy.fragment
    def capture(v):
        output.append(v)
    seq.append(capture)

    chain = spy.chain(seq, bootstrap=['foo', 'bar'])
    chain.run_to_exhaustion()
    assert output == ['OOF', 'RAB']


def test_defaults(capsys):
    stream = StringIO('some\ntest\ndata')
    chain = spy.chain.with_defaults([many], stream=stream)
    chain.run_to_exhaustion()
    out, err = capsys.readouterr()
    assert out == 'some\ntest\ndata\n'


def test_many():
    seq = [many, upper]
    chain = spy.chain(seq, bootstrap=['foo', 'bar'])
    assert list(chain) == list('FOOBAR')


def test_collect():
    seq = [collect]
    chain = spy.chain(seq, bootstrap=['foo', 'bar'])
    assert list(next(chain)) == ['foo', 'bar']


def test_drop():
    seq = [drop_foo]
    chain = spy.chain(seq, bootstrap=['foo', 'bar', 'foo', 'test'])
    for item in chain:
        assert item.lower() != 'foo'


def test_raw():
    r = spy.raw('abcdef')
    assert repr(r) == 'abcdef'
