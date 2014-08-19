from builtins import print as py_print
from collections import Iterable, Mapping, Sequence
from itertools import chain, islice

import sys

from . import core


def many(ita):
    return chain.from_iterable(ita)


def make_limit(*, start=0, end=None):
    def limit(ita):
        return islice(ita, start, end)
    return limit


def pretty_print(thing):
    if isinstance(thing, str):
        _write(thing)
        _write('\n')
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
    global _write
    _write = sys.stdout.write
    return map(pretty_print, ita)
