import itertools
import traceback

from functools import wraps

from . import fragments

import dis, sys


_iteration_state = None


def _call_fragment_body(f, *a, **kw):
    return f(*a, **kw)


class _Drop:
    pass
DROP = _Drop()


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
    def __init__(self, seq, init=[None], index_offset=0):
        self.ita = init
        for i, step in enumerate(seq):
            try:
                self.ita = step(self.ita, i + index_offset + 1)
            except:
                self.ita = step(self.ita)
        self._iter = iter(self.ita)
        self._next = self._iter.__next__

    @classmethod
    def with_defaults(cls, seq, *, stream=None, **kw):
        start = []
        if stream is not None:
            start.append(fragments.init(stream))
        return cls(itertools.chain(start, seq, [fragments.print]),
                   index_offset=-len(start), **kw)

    def run_to_exhaustion(self):
        for item in self.ita:
            pass

    def __iter__(self):
        return self._iter

    def __next__(self):
        return self._next()


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
