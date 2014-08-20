from functools import wraps
import inspect

from .core import _call_fragment_body, collect, DROP, many as _many

__all__ = ['callable', 'filter', 'many', 'once']

decorators = []


def decorator(*names, doc=None):
    def wrapperer(dec):
        @wraps(dec)
        def wrapper(fn):
            @wraps(fn)
            def wrapped(v, context=None):
                _spy_decorator = dec
                _spy_callable = fn
                _spy_value = v
                return dec(fn, v, context)
            return wrapped
        wrapper.decorator_names = names
        wrapper.decorator_help = doc
        decorators.append(wrapper)
        return wrapper
    return wrapperer


def call_fragment(fn, v, context):
    with_context = getattr(fn, '_spy_with_context', None)
    if with_context is None:
        argspec = inspect.getfullargspec(fn)
        fn._spy_with_context = with_context = (len(argspec.args) >= 2 or
            argspec.varargs or argspec.varkw or 'context' in argspec.kwonlyargs)
    if with_context:
        return _call_fragment_body(fn, v, context=context)
    else:
        return _call_fragment_body(fn, v)


@decorator('--callable', '-c', doc='Call the result of this fragment')
def callable(fn, v, context):
    result = call_fragment(fn, v, context)
    return result(v)


@decorator('--filter', '-f', doc='Treat this fragment as a predicate to filter data')
def filter(fn, v, context):
    result = call_fragment(fn, v, context)
    return v if result else DROP


@decorator('--many', '-m', doc='Iterate over this fragment')
def many(fn, v, context):
    result = call_fragment(fn, v, context)
    return _many(result)


@decorator('--once', '-o', doc='Run this fragment at most once, and ignore its result')
def once(fn, v, context):
    call_fragment(fn, v, context)
    return _many(collect(context))
