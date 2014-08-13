context = None

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
