from functools import partial, wraps, update_wrapper
import copy
import re
import string

from .core import _accepts_context, _call_fragment_body, collect, DROP, many as _many

__all__ = ['accumulate', 'callable', 'filter', 'many', 'format', 'regex', 'keywords']

decorators = []


def decorator(*names, doc=None, takes_string=False, prep=None, dec_args=()):
    if prep is None:
        if len(dec_args) == 1:
            prep = lambda _, a: a
        elif len(dec_args) > 1:
            prep = lambda _, *a: a

    def wrapperer(_spy_decorator):
        @wraps(_spy_decorator)
        def wrapper(fn, dec_args=()):
            if _accepts_context(fn):
                xfn = partial(_call_fragment_body, fn)
            else:
                xfn = partial(_drop_context, fn)

            if prep:
                opaque = prep(fn, *dec_args)
                def wrapped(v, context=None):
                    _spy_callable = fn  # noqa: F841
                    _spy_value = v  # noqa: F841
                    return _spy_decorator(xfn, v, context, opaque)
            else:
                def wrapped(v, context=None):
                    _spy_callable = fn  # noqa: F841
                    _spy_value = v  # noqa: F841
                    return _spy_decorator(xfn, v, context)
            update_wrapper(wrapped, fn)
            return wrapped

        if dec_args:
            orig_wrapper = wrapper
            def wrapper(*a):
                return partial(orig_wrapper, dec_args=a)

        wrapper.decorator_names = names
        wrapper.decorator_help = doc
        wrapper.takes_string = takes_string
        wrapper.dec_args = dec_args
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


_formatter = string.Formatter()

@decorator('--format', '-i', doc='Interpolate argument as a format string', takes_string=True)
def format(fn, v, context):
    env, x = fn(v, context)
    return _formatter.vformat(x, v, env)


@decorator('--regex', '--regexp', '-R', doc='Match argument as a regexp', takes_string=True)
def regex(fn, v, context):
    env, x = fn(v, context)
    return re.match(x, v)


def _kw_prep(fn):
    base = fn
    while hasattr(base, '__wrapped__'):
        base = base.__wrapped__
    if not hasattr(base, '_spy_setenv'):
        raise ValueError("inappropriate function")
    return base._spy_setenv


@decorator('--keywords', '-k', doc='Execute with the input value as the scope', prep=_kw_prep)
def keywords(fn, v, context, setenv):
    setenv(v)
    return fn(v, context)


def _convert_focus(s):
    if s[:1] in '0123456789-' and (len(s) == 1 or s[1:].isdigit()):
        return int(s)
    return s
_convert_focus.usage_name = 'ITEM'


@decorator('--magnify', '-O', doc='Operate on and return an item of the input', dec_args=[_convert_focus])
def magnify(fn, v, context, item):
    return fn(v[item], context)


@decorator('--focus', '-o', doc='Operate on an item of the input in-place', dec_args=[_convert_focus])
def focus(fn, v, context, item):
    v_ = fn(v[item], context)
    v = copy.copy(v)
    v[item] = v_
    return v
