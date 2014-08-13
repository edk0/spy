from builtins import print as py_print

def many(ita, context):
    for item in ita:
        yield from item


def make_limit(*, start=0, end=None):
    def limit(ita, context):
        for n, item in enumerate(ita):
            if n >= start and (end is None or n < end):
                yield item
            elif end is not None and n >= end:
                yield '...'
                break
    return limit


def print(ita, context):
    for item in ita:
        py_print(item)
        yield item
