from builtins import print as py_print
from collections import Iterable, Mapping, Sequence
from itertools import chain, islice

import sys
py_write = sys.stdout.write

from .objects import SpyFile


def init(ita):
    yield SpyFile(sys.stdin)


def many(ita):
    return chain.from_iterable(ita)


def make_limit(*, start=0, end=None):
    def limit(ita):
        for n, item in enumerate(ita):
            if n >= start and (end is None or n < end):
                yield item
            elif end is not None and n >= end:
                yield '...'
                break
    return limit


def pretty_print(thing):
    if isinstance(thing, str):
        py_write(thing)
        py_write('\n')
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


def print(ita):
    for item in ita:
        pretty_print(item)
        yield item
