import numbers
import inspect
import itertools


def _accepts_context(fn):
    argspec = inspect.getfullargspec(fn)
    return (len(argspec.args) >= 2 or argspec.varargs)


def _call_fragment_body(f, *a, **kw):
    return f(*a, **kw)


class _Constant:
    pass


DROP = _Constant()


class _Context:
    __slots__ = ('iter_value', 'iter_iter')

    def __init__(self, iter_value, iter_iter):
        self.iter_value = iter_value
        self.iter_iter = iter_iter


def fragment(fn):
    with_context = _accepts_context(fn)

    def fragment(ita, index=None):
        ita = iter(ita)
        _spy_fragment_index = index  # noqa: F841
        if with_context:
            context = _Context(None, ita)
        for _spy_value in ita:
            if with_context:
                context.iter_value = _spy_value
                result = fn(_spy_value, context)
            else:
                result = fn(_spy_value)
            if result is DROP:
                continue
            elif isinstance(result, many):
                yield from result.ita
            else:
                yield result
    fragment.fragment_fn = fn
    return fragment


step = fragment


class chain:
    def __init__(self, seq, index_offset=0):
        self.seq = seq
        if not isinstance(index_offset, numbers.Integral):
            raise TypeError('index_offset must be integral')
        self.index_offset = index_offset

    @classmethod
    def auto_fragments(cls, seq, **kw):
        def make_fragment(f):
            if hasattr(f, '__code__') and f.__code__.co_flags & 0x20:
                return f
            else:
                return fragment(f)
        return cls(map(make_fragment, seq), **kw)

    @classmethod
    def with_defaults(cls, seq, **kw):
        from . import fragments
        return cls(itertools.chain(seq, [fragments.print]), **kw)

    def apply(self, ita):
        for i, step in enumerate(self.seq):
            try:
                ita = step(ita, index=i + self.index_offset + 1)
            except TypeError:
                ita = step(ita)
        yield from ita

    __call__ = apply

    def run_to_exhaustion(self, *a, **kw):
        for item in self.apply(*a, **kw):
            pass

    def format(self):
        l = []
        for n, step in enumerate(self.seq):
            i = n + self.index_offset + 1
            if i < 1:
                i = ''
            if hasattr(step, 'fragment_fn') and hasattr(step.fragment_fn, '_spy_debuginfo'):
                desc = step.fragment_fn._spy_debuginfo[1]
            else:
                if hasattr(step, 'fragment_fn'):
                    step = step.fragment_fn
                    typ = ''
                if hasattr(step, '__qualname__'):
                    name = step.__qualname__
                    typ = '<internal> '
                else:
                    name = 'UNKNOWN'
                if hasattr(step, '__module__'):
                    name = step.__module__ + '.' + name
                desc = typ + name
            l.append('{:3} | {}'.format(i, desc))
        return '\n'.join(l)


class many:
    def __init__(self, ita):
        self.ita = ita


def collect(context):
    if context is None:
        raise ValueError("Can't collect without a valid context (got None)")
    return itertools.chain([context.iter_value], context.iter_iter)


collect._spy_inject_context_ = True
