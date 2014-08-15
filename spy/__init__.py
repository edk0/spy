import itertools
import traceback

from functools import wraps

import spy.fragments


context = None
_iteration_state = []


class _Drop:
    pass
DROP = _Drop()


def fragment(fn):
    @wraps(fn)
    def fragment(ita, index=None):
        ita = iter(ita)
        _spy_fragment_index = index
        for item in ita:
            _spy_value = item
            _iteration_state.append((item, ita))
            result = fn(item)
            _iteration_state.pop()
            if result is DROP:
                continue
            elif isinstance(result, many):
                for result in iter(result):
                    yield result
            else:
                yield result
    return fragment

step = fragment


class chain:
    def __init__(self, seq, bootstrap=(None,), index_start=1):
        self.ita = bootstrap
        for i, step in enumerate(seq):
            try:
                self.ita = step(self.ita, i)
            except:
                self.ita = step(self.ita)

    @classmethod
    def with_defaults(cls, seq, **kw):
        return cls(itertools.chain([spy.fragments.init], seq, [spy.fragments.print]), index_start=0, **kw)

    def run_to_exhaustion(self):
        for item in self:
            pass

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.ita)


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
    init, ita = _iteration_state[-1]
    def collector():
        yield init
        for item in ita:
            yield item
    return collector()
