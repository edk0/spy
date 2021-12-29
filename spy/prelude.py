import builtins
from functools import partial, reduce
from itertools import chain, islice, starmap
from operator import iadd


__all__ = ['id', 'ft', 'mt', 'sum', 'exhaust']


def id(x):
    return x


class ft(tuple):
    def __new__(self, *a):
        return tuple.__new__(ft, a)
    def __call__(self, x):
        return tuple(f(x) for f in self)


class mt(tuple):
    def __new__(self, *funcs):
        return tuple.__new__(mt, funcs)
    def __call__(self, xs):
        return tuple(f(x) for f, x in zip(self, xs))


def exhaust(ita):
    for _ in ita:
        pass


_builtin_sum = builtins.sum

_sentinel = object()

def sum(iterable, start=_sentinel):
    if start is _sentinel:
        iterable = iter(iterable)
        try:
            start = next(iterable)
        except StopIteration:
            start = 0
    if isinstance(start, (int, float)):
        return _builtin_sum(iterable, start)
    if isinstance(start, (str, bytes, bytearray)):
        return type(start)().join(chain((start,), iterable))
    iterable = iter(iterable)
    return reduce(iadd, iterable,
            _builtin_sum(islice(iterable, 1), start))

builtins.sum = sum
