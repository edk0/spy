import itertools
import traceback

from functools import wraps


from .objects import SpyFile


_iteration_state = None


def _call_fragment_body(f, *a, **kw):
    return f(*a, **kw)


class _Constant:
    pass

DROP = _Constant()


def fragment(fn):
    def fragment(ita, index=None):
        global _iteration_state
        ita = iter(ita)
        _spy_fragment_index = index
        for _spy_value in ita:
            _iteration_state = (_spy_value, ita)
            result = fn(_spy_value)
            if result is DROP:
                continue
            elif isinstance(result, many):
                for result in result.ita:
                    yield result
            else:
                yield result
    return fragment

step = fragment


class chain:
    def __init__(self, seq, index_offset=0):
        self.seq = seq
        self.index_offset = index_offset

    @classmethod
    def with_defaults(cls, seq, **kw):
        from . import fragments
        return cls(itertools.chain(seq, [fragments.print]), **kw)

    def apply(self, ita):
        for i, step in enumerate(self.seq):
            try:
                ita = step(ita, index=i + self.index_offset + 1)
            except TypeError:
                ita = step(ita)
        for item in ita:
            yield item

    def run_to_exhaustion(self, *a, **kw):
        for item in self.apply(*a, **kw):
            pass


class raw:
    def __init__(self, s):
        self.s = str(s)

    def __repr__(self):
        return self.s


class many:
    def __init__(self, ita):
        self.ita = ita

    def __iter__(self):
        return iter(self.ita)


def collect():
    init, ita = _iteration_state
    return itertools.chain([init], ita)
