from bisect import bisect_left
from functools import wraps
from importlib import import_module
import io
from io import TextIOBase, UnsupportedOperation
from reprlib import recursive_repr
from types import ModuleType
import operator
import math


class _Wrapper(dict):
    def __missing__(self, x):
        if hasattr(x, '__call__'):
            self[x] = w = _FunctionWrapper(x)
            return w
        self[x] = x
        return x

def _wrap(x, _wrapper=_Wrapper()):
    try:
        return _wrapper[x]
    except TypeError:
        return x


class _ModuleProxy:
    __slots__ = ('_ModuleProxy__module',)

    def __init__(self, module):
        self.__module = module

    def __getattr__(self, k):
        try:
            v = getattr(self.__module, k)
        except AttributeError as e:
            try:
                v = import_module('.' + k, self.__module.__name__)
            except ImportError:
                e._forced_ = True
                raise e
        if isinstance(v, ModuleType):
            return self.__class__(v)
        else:
            return _wrap(v)

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


class _FunctionWrapper:
    __slots__ = ('_function', 'name')

    def _proxy_unop(op):
        name = op.__name__ + '(%s)'
        def fn(self):
            f = self._function
            try:
                return op(f)
            except TypeError:
                pass
            return _FunctionWrapper(lambda x: op(f(x)), name % f.__name__)
        return fn

    def _proxy_binop(op, only_missing=True):
        name = op.__name__ + '(%s,%s)'
        def fn(self, other):
            f = self._function
            o = other
            call_other = False
            if isinstance(other, _FunctionWrapper):
                other = other._function
                call_other = True
            elif hasattr(other, '__call__'):
                call_other = True
            if only_missing:
                try:
                    return op(f, other)
                except TypeError:
                    pass
            if call_other:
                return _FunctionWrapper(lambda x: op(f(x), other(x)), name % (self.__name__, o.__name__))
            else:
                return _FunctionWrapper(lambda x: op(f(x), other), name % (self.__name__, repr(other)))
        def rfn(self, other):
            f = self._function
            o = other
            call_other = False
            if hasattr(other, '__call__'):
                call_other = True
            try:
                return op(other, f)
            except TypeError:
                pass
            if call_other:
                return _FunctionWrapper(lambda x: op(other(x), f(x)), name % (o.__name__, self.__name__))
            else:
                return _FunctionWrapper(lambda x: op(other, f(x)), name % (repr(other), self.__name__))
        return fn, rfn

    def __init__(self, function, name=None):
        self._function = function
        self.name = name

    @property
    def __name__(self):
        if self.name is not None:
            return self.name
        return self._function.__name__

    def __getattr__(self, k):
        return getattr(self._function, k)

    def __call__(self, *a, **kw):
        return self._function(*a, **kw)

    def __repr__(self):
        if self.name is not None:
            return self.name
        return repr(self._function)

    __eq__, _ = _proxy_binop(operator.eq, only_missing=False)
    __ne__, _ = _proxy_binop(operator.ne, only_missing=False)
    __lt__, _ = _proxy_binop(operator.lt)
    __le__, _ = _proxy_binop(operator.le)
    __gt__, _ = _proxy_binop(operator.gt)
    __ge__, _ = _proxy_binop(operator.ge)
    del _
    __add__, __radd__ = _proxy_binop(operator.add)
    __sub__, __rsub__ = _proxy_binop(operator.sub)
    __mul__, __rmul__ = _proxy_binop(operator.mul)
    __matmul__, __rmatmul__ = _proxy_binop(operator.matmul)
    __truediv__, __rtruediv__ = _proxy_binop(operator.truediv)
    __floordiv__, __rfloordiv__ = _proxy_binop(operator.floordiv)
    __mod__, __rmod__ = _proxy_binop(operator.mod)
    __divmod__, __rdivmod__ = _proxy_binop(divmod)
    __pow__, __rpow__ = _proxy_binop(operator.pow)
    __lshift__, __rlshift__ = _proxy_binop(operator.lshift)
    __rshift__, __rrshift__ = _proxy_binop(operator.rshift)
    __and__, __rand__ = _proxy_binop(operator.and_)
    __xor__, __rxor__ = _proxy_binop(operator.xor)
    __or__, __ror__ = _proxy_binop(operator.or_)

    __neg__ = _proxy_unop(operator.neg)
    __pos__ = _proxy_unop(operator.pos)
    __abs__ = _proxy_unop(abs)
    __invert__ = _proxy_unop(operator.invert)
    __int__ = _proxy_unop(int)
    __trunc__ = _proxy_unop(math.trunc)
    __floor__ = _proxy_unop(math.floor)
    __ceil__ = _proxy_unop(math.ceil)


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
            return _wrap(self.overlay[k])
        return _wrap(self.context[k])

    def __setitem__(self, k, v):
        if k in self.overlay:
            self.overlay[k] = v
        else:
            self.context[k] = v

    def __delitem__(self, k):
        if k in self.overlay:
            raise TypeError("can't delete: {!r}".format(k))
        del self.context[k]

    def get(self, k, default):
        try:
            return self[k]
        except LookupError:
            return default

    @recursive_repr()
    def __repr__(self):
        return '{}(context={}, overlay={})'.format(
            self.__class__.__name__, repr(self.context), repr(self.overlay))


class SpyFile(TextIOBase):
    def __init__(self, stream):
        self.stream = stream
        self.lines = []
        self.row = 0
        self.col = 0
        self.rowoff = [0]
        self.offset = 0
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

    def __len__(self):
        while self._read_one():
            pass
        return len(self.lines)

    def __str__(self):
        while self._read_one():
            pass
        return '\n'.join(self.lines)

    def __repr__(self):
        name = getattr(self.stream, 'name', self.stream)
        return '<SpyFile stream={!r}>'.format(name)

    def __iter__(self):
        return SpyFileReader(self)

    def _line_iter(self):
        return (l.rstrip('\n') for l in self.stream)

    def _read_one(self):
        try:
            l = self._next().rstrip('\n')
            self.rowoff.append(self.rowoff[-1] + len(l) + 1)
            self._append(l)
            return True
        except StopIteration:
            return False

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            pass
        elif whence == io.SEEK_CUR:
            offset += self.offset
        elif whence == io.SEEK_END:
            while self._read_one():
                pass
            offset += self.rowoff[-1]
        else:
            raise ValueError
        if offset < 0:
            offset = 0
        while self.rowoff[-1] < offset and self._read_one():
            pass
        if offset > self.rowoff[-1]:
            offset = self.rowoff[-1]
        row = bisect_left(self.rowoff, offset)
        ro = self.rowoff[row]
        if offset < ro:
            row -= 1
        self.row = row
        self.col = offset - self.rowoff[row]
        return offset

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
        self.offset += len(buf)
        return buf

    def readline(self, n=-1):
        try:
            row = self[self.row][self.col:] + '\n'
        except IndexError:
            return ''
        if len(row) >= n >= 0:
            self.col += n
            self.offset += n
            return row[:n]
        else:
            self.row += 1
            self.col = 0
            self.offset += len(row)
            return row

    def detach(self):
        raise UnsupportedOperation


class SpyFileReader:
    def __init__(self, spyfile):
        self._spyfile = spyfile
        self._row = 0

    def __iter__(self):
        return self

    def __next__(self):
        row = self._row
        self._row += 1
        try:
            return self._spyfile[row]
        except IndexError:
            raise StopIteration
