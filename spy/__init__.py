import traceback

PIPE_NAME = 'pipe'


context = None
_iteration_state = None


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
    init, ita = _iteration_state
    def collector():
        yield init
        for item in ita:
            yield item
    return collector()
