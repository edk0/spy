from functools import wraps

from .core import _call_fragment_body, DROP, many as _many

__all__ = ['callable', 'filter']

decorators = []


def decorator(*names, doc=None):
    def wrapperer(dec):
        @wraps(dec)
        def wrapper(fn):
            @wraps(fn)
            def wrapped(v):
                _spy_decorator = dec
                _spy_callable = fn
                _spy_value = v
                return dec(fn, v)
            return wrapped
        wrapper.decorator_names = names
        wrapper.decorator_help = doc
        decorators.append(wrapper)
        return wrapper
    return wrapperer


@decorator('--callable', '-c', doc='Call the result following fragment')
def callable(fn, v):
    result = _call_fragment_body(fn, v)
    return result(v)


@decorator('--filter', '-f', doc='Treat the fragment as a predicate to filter data')
def filter(fn, v):
    result = _call_fragment_body(fn, v)
    return v if result else DROP


@decorator('--many', '-m', doc='Return a value from this fragment for each element of an iterable')
def many(fn, v):
    result = _call_fragment_body(fn, v)
    return _many(result)
