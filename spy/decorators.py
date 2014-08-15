from functools import wraps

import spy

decorators = []


def decorator(*names):
    def wrapperer(dec):
        @wraps(dec)
        def wrapper(fn, debuginfo=(None, None)):
            @wraps(fn)
            def wrapped(v):
                _spy_debuginfo = debuginfo + (v,)
                return dec(fn, v)
            return wrapped
        wrapper.decorator_names = names
        decorators.append(wrapper)
        return wrapper
    return wrapperer


@decorator('--callable', '-c')
def callable(fn, v):
    result = fn(v)
    return result(v)


@decorator('--filter', '-f')
def filter(fn, v):
    result = fn(v)
    return v if result else spy.DROP
