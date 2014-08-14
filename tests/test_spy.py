import spy


@spy.step
def noop(v):
    return v


@spy.step
def upper(v):
    return v.upper()


@spy.step
def reverse(v):
    return v[::-1]


@spy.step
def drop_foo(v):
    if v.lower() == 'foo':
        return spy.DROP
    return v


@spy.step
def many(v):
    return spy.many(v)


@spy.step
def collect(v):
    return spy.collect()


def test_chain():
    seq = [noop, upper, noop, reverse, noop]
    chain = spy.chain(seq, bootstrap=['foo', 'bar'])
    assert list(chain) == ['OOF', 'RAB']


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
