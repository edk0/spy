from collections.abc import Mapping
from io import TextIOBase
from reprlib import recursive_repr


class Context(dict):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

    def __iadd__(self, other):
        if isinstance(other, Mapping):
            self.update(other)
            return self
        else:
            return NotImplemented

    @recursive_repr()
    def __repr__(self):
        d = {k: v for k, v in self.items() if not k.startswith('_')}
        return '{}({})'.format(self.__class__.__qualname__, repr(d))


class _SpyFile_Iterator:
    def __init__(self, f):
        self.f = f
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.index += 1
            return self.f[self.index - 1]
        except IndexError:
            raise StopIteration


class SpyFile(TextIOBase):
    def __init__(self, stream):
        self.stream = stream
        self.lines = []
        self.buffer_ = None

    def __iter__(self):
        return _SpyFile_Iterator(self)

    def __len__(self):
        for _ in self:
            pass
        return len(self.lines)

    def __getitem__(self, k):
        if isinstance(k, slice):
            while self._readline():
                pass
            return self.lines[k]
        while self._readline():
            if len(self.lines) > k:
                break
        if len(self.lines) > k:
            return self.lines[k]
        raise IndexError(k)

    def __getattr__(self, k):
        if hasattr(str, k):
            return getattr(str(self), k)
        raise AttributeError(k)

    def __str__(self):
        while self._readline():
            pass
        return '\n'.join(self.lines)

    def __repr__(self):
        return repr(str(self))

    def _readline(self):
        try:
            l = next(self.stream)
            self.lines.append(l[:-1])
            if self.buffer_ is not None:
                self.buffer_ += l
            return l[:-1]
        except StopIteration:
            return ''

    def read(self, n=None):
        if n == 0:
            return ''
        if self.buffer_ is None:
            self.buffer_ = '\n'.join(self.lines)
        while self._readline():
            if n is not None and n >= 0 and len(self.buffer_) >= n:
                v = self.buffer_[:n]
                self.buffer_ = self.buffer_[n:]
                return v
        if n is None or n < 0:
            v = self.buffer_[:]
            self.buffer_ = ''
            return v

    def readline(self, n=-1):
        if n < 0:
            try:
                return self._readline()
            except StopIteration:
                return ''
        s = self.read(n)
        if '\n' in s:
            s, extra = s.split('\n', 1)
            self.buffer_ = extra + self.buffer_
            return s + '\n'

    def detach(self):
        raise UnsupportedOperation

