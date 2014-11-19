from collections import Mapping
from functools import wraps
from importlib import import_module
from io import TextIOBase, UnsupportedOperation
from reprlib import recursive_repr
from types import ModuleType


class _ModuleProxy:
    __slots__ = ('_ModuleProxy__module',)

    def __init__(self, module):
        self.__module = module

    def __getattr__(self, k):
        try:
            v = getattr(self.__module, k)
        except AttributeError:
            v = import_module('.' + k, self.__module.__name__)
        if isinstance(v, ModuleType):
            return self.__class__(v)
        else:
            return v

    def __setattr__(self, k, v):
        if '__' in k and k.split('__', 1)[0].startswith('_'):
            object.__setattr__(self, k, v)
        else:
            setattr(self.__module, k, v)

    def __delattr__(self, k):
        delattr(self.__module, k)

    def __dir__(self):
        return dir(self.__module)

    def __repr__(self):
        return repr(self.__module)


class _ContextInjector(_ModuleProxy):
    __slots__ = ('_ContextInjector__context',)

    def __init__(self, module):
        super().__init__(module)
        self.__context = None

    def __getattr__(self, k):
        v = super().__getattr__(k)
        if getattr(v, '_spy_inject_context_', None) is True:
            @wraps(v)
            def wrapper(*a, **kw):
                if 'context' not in kw:
                    kw['context'] = self.__context
                return v(*a, **kw)
            return wrapper
        else:
            return v


class Context(dict):
    __slots__ = ()

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

    def __missing__(self, k):
        try:
            module = self[k] = _ModuleProxy(import_module(k))
            return module
        except ImportError:
            raise KeyError

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
    __slots__ = ('stream', 'lines', 'row', 'col', '_append', '_next')

    def __init__(self, stream):
        self.stream = stream
        self.lines = []
        self.row = 0
        self.col = 0
        self._append = self.lines.append
        self._next = iter(self.stream).__next__

    def __getitem__(self, k):
        if isinstance(k, slice):
            while self._read_one():
                pass
            return self.lines[k]
        while self._read_one():
            if len(self.lines) > k:
                break
        if len(self.lines) > k:
            return self.lines[k]
        raise IndexError(k)

    def __str__(self):
        while self._read_one():
            pass
        return '\n'.join(self.lines)

    def __repr__(self):
        name = getattr(self.stream, 'name', self.stream)
        return '<SpyFile stream={!r}>'.format(name)

    def __iter__(self):
        return (l.rstrip('\n') for l in self.stream)

    def _read_one(self):
        try:
            l = self._next().rstrip('\n')
            self._append(l)
            return True
        except StopIteration:
            return False

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
