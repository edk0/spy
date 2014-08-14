import traceback


context = None
_iteration_state = []


class _Drop:
    pass
DROP = _Drop()


def step(fn):
    def step(ita):
        ita = iter(ita)
        for item in ita:
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
    return step


class chain:
    def __init__(self, seq, bootstrap=(None,)):
        self.ita = bootstrap
        for step in seq:
            self.ita = step(self.ita)

    def run_to_exhaustion(self):
        for item in self.ita:
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
