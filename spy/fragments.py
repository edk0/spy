from builtins import print as py_print
from collections import Iterable, Mapping, Sequence
from itertools import islice

import sys

from .objects import SpyFile
from spy import raw


def init(ita):
    yield SpyFile(sys.stdin)


def many(ita):
    for thing in ita:
        for item in thing:
            yield item


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
        py_print(thing)
    elif not isinstance(thing, (Mapping, Sequence)) and isinstance(thing, Iterable):
        sliced = []
        for n, item in enumerate(thing):
            if n < 5:
                sliced.append(item)
            else:
                sliced.append(raw('...'))
                break
        py_print("<iterable {}>".format(repr(sliced)))
    else:
        sys.displayhook(thing)


def print(ita):
    for item in ita:
        pretty_print(item)
        yield item
