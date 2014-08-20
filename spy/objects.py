from collections import Mapping
from io import TextIOBase, UnsupportedOperation
from reprlib import recursive_repr


class Context(dict):
    def __init__(self, *a, _pipe_name, **kw):
        self.pipe_name = _pipe_name
        super().__init__(*a, **kw)

    def __iadd__(self, other):
        if isinstance(other, Mapping):
            self.update(other)
            return self
        else:
            return NotImplemented

    def pipe_view(self, value):
        return _ContextView(self, value)

    @recursive_repr()
    def __repr__(self):
        d = {k: v for k, v in self.items() if not k.startswith('_')}
        return '{}({})'.format(self.__class__.__name__, repr(d))


class _ContextView:
    def __init__(self, context, value):
        self.context = context
        self.value = value
        self.overlay = {}
        self._debuginfo = (None, None)

    def __contains__(self, k):
        return k == self.context.pipe_name or k in self.context

    def __getitem__(self, k):
        if k == self.context.pipe_name:
            return self.value
        elif k in self.overlay:
            return self.overlay[k]
        return self.context[k]

    def __setitem__(self, k, v):
        if k == self.context.pipe_name:
            self.value = v
        else:
            self.context[k] = v

    def __delitem__(self, k):
        if k == self.context.pipe_name:
            raise TypeError("can't delete pipe")
        del self.context[k]

    @recursive_repr()
    def __repr__(self):
        return '{}(context={}, value={})'.format(self.__class__.__name__,
                repr(self.context), repr(self.value))


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
        return '<SpyFile stream={!r}>'.format(self.stream)

    def __iter__(self):
        return self

    def __next__(self):
        l = self._next()
        if l[-1] == '\n':
            l = l[:-1]
        self._append(l)
        return l

    def _readline(self):
        try:
            return next(self)
        except StopIteration:
            return ''

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
