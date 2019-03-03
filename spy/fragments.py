from builtins import print as py_print
from collections.abc import Iterable, Mapping, Sequence
from itertools import islice

import sys

from .objects import SpyFile


def stdin(ita):
    yield SpyFile(sys.stdin)


def raw_stdin(ita):
    yield sys.stdin


def foreach(ita):
    for elem in ita:
        if isinstance(elem, SpyFile):
            yield from elem._line_iter()
        else:
            yield from elem


def make_limit(*, start=0, end=None):
    def limit(ita):
        return islice(ita, start, end)
    return limit


def pretty_print(thing):
    if isinstance(thing, str):
        py_print(thing)
    elif not isinstance(thing, (Mapping, Sequence)) and isinstance(thing, Iterable):
        sliced = []
        for n, item in enumerate(thing):
            if n < 5:
                sliced.append(repr(item))
            else:
                sliced.append('...')
                break
        py_print("<iterable [{}]>".format(', '.join(sliced)))
    else:
        sys.displayhook(thing)
    return thing


def print(ita):
    return map(pretty_print, ita)
