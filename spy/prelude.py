from functools import partial
from itertools import starmap


__all__ = ['id', 'ft', 'mt']


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
