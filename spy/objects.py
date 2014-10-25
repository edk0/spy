from collections import Mapping
from io import TextIOBase, UnsupportedOperation
from reprlib import recursive_repr


class Context(dict):
    __slots__ = ()

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

    def view(self):
        return _ContextView(self)

    @recursive_repr()
    def __repr__(self):
        d = {k: v for k, v in self.items() if not k.startswith('_')}
        return '{}({})'.format(self.__class__.__name__, repr(d))


class _ContextView:
    __slots__ = ('context', 'overlay', '_spy_debuginfo')

    def __init__(self, context):
        self.context = context
        self.overlay = {}

    def __contains__(self, k):
        return k in self.overlay or k in self.context

    def __getitem__(self, k):
        if k in self.overlay:
            return self.overlay[k]
        return self.context[k]

    def __setitem__(self, k, v):
        if k in self.overlay:
            self.overlay[k] = v
        else:
            self.context[k] = v

    def __delitem__(self, k):
        if k in self.overlay:
            raise TypeError("can't delete: {!r}".format(k))
        del self.context[k]

    @recursive_repr()
    def __repr__(self):
        return '{}(context={}, overlay={})'.format(self.__class__.__name__,
                repr(self.context), repr(self.overlay))


class SpyFile(TextIOBase):
    def __init__(self, stream):
        self.stream = stream
        self.lines = []
        self.row = 0
        self.col = 0
        self._append = self.lines.append
        self._next = iter(self.stream).__next__

    def __len__(self):
        return NotImplemented

    def __getitem__(self, k):
        if isinstance(k, slice):
            for _ in self:
                pass
            return self.lines[k]
        for _ in self:
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
        for _ in self:
            pass
        return '\n'.join(self.lines)

    def __repr__(self):
        return '<SpyFile stream={!r}>'.format(self.stream)

    def __iter__(self):
        return self

    def __next__(self):
        l = self._next()
        if l[-1] == '\n':
            l = l[:-1]
        self._append(l)
        return l

    def read(self, n=None):
        if n == 0:
            return ''
        buf = ''
        try:
            while n is None or len(buf) < n:
                row = self[self.row]
                try:
                    self[self.row + 1]
                    row += '\n'
                except IndexError:
                    pass
                start = self.col
                if n is not None:
                    end = start + n - len(buf)
                    buf += row[start:end]
                else:
                    buf += row[start:]
                if n is None or end >= len(row):
                    self.row += 1
                    self.col = 0
                else:
                    self.col = end
        except IndexError:
            pass
        return buf

    def readline(self, n=-1):
        try:
            row = self[self.row][self.col:] + '\n'
        except IndexError:
            return ''
        if len(row) >= n >= 0:
            self.col += n
            return row[:n]
        else:
            self.row += 1
            self.col = 0
            return row

    def detach(self):
        raise UnsupportedOperation
