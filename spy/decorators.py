from functools import wraps

from .core import _call_fragment_body, DROP

__all__ = ['callable', 'filter']

decorators = []


def decorator(*names):
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
        decorators.append(wrapper)
        return wrapper
    return wrapperer


@decorator('--callable', '-c')
def callable(fn, v):
    result = _call_fragment_body(fn, v)
    return result(v)


@decorator('--filter', '-f')
def filter(fn, v):
    result = _call_fragment_body(fn, v)
    return v if result else DROP
