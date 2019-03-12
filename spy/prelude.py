def id(x):
    return x

class ft(tuple):
    def __new__(self, *a):
        return tuple.__new__(ft, a)
    def __call__(self, x):
        return tuple(f(x) for f in self)
