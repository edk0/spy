import traceback

PIPE_NAME = 'pipe'


context = None
_iteration_state = []


def step(fn):
    def step(ita):
        for item in ita:
            _iteration_state.append((item, ita))
            result = fn(item)
            _iteration_state.pop()
            if result is DROP:
                continue
            elif isinstance(result, many):
                for result in result.ita:
                    yield result
            else:
                yield result
    return step


def chain(seq, bootstrap=(None,)):
    ita = bootstrap
    for step in seq:
        ita = step(ita)
    for item in ita:
        yield item


class _Drop:
    pass
DROP = _Drop()


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
