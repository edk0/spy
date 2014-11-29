from functools import partial, wraps
import sys

from .core import _accepts_context, _call_fragment_body, collect, DROP, many as _many

__all__ = ['accumulate', 'callable', 'filter', 'many']

decorators = []


def decorator(*names, doc=None):
    def wrapperer(_spy_decorator):
        @wraps(_spy_decorator)
        def wrapper(fn):
            if _accepts_context(fn):
                xfn = partial(_call_fragment_body, fn)
            else:
                xfn = partial(_drop_context, fn)
            @wraps(fn)
            def wrapped(v, context=None):
                _spy_callable = fn
                _spy_value = v
                return _spy_decorator(xfn, v, context)
            return wrapped
        wrapper.decorator_names = names
        wrapper.decorator_help = doc
        decorators.append(wrapper)
        return wrapper
    return wrapperer


def _drop_context(fn, v, context):
    return _call_fragment_body(fn, v)


@decorator('--accumulate', '-a', doc='Pass an iterator of yielded values to this fragment')
def accumulate(fn, v, context):
    return fn(collect(context), context)


@decorator('--callable', '-c', doc='Call the result of this fragment')
def callable(fn, v, context):
    result = fn(v, context)
    return result(v)


@decorator('--filter', '-f', doc='Treat this fragment as a predicate to filter data')
def filter(fn, v, context):
    result = fn(v, context)
    return v if result else DROP


@decorator('--many', '-m', doc='Iterate over this fragment')
def many(fn, v, context):
    result = fn(v, context)
    return _many(result)
