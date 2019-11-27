import inspect
import itertools
import sys
import traceback

from . import core
from .objects import Context


class CaughtException(Exception):
    def __init__(self, formatted_tb):
        self.formatted_tb = formatted_tb

    def print_traceback(self):
        _print(self.formatted_tb)

    def __str__(self):
        return ''


def _format_exc(typ, exc, tb, *, delete_all=False):
    hide_below_user = False
    if getattr(exc, '_forced_', False):
        hide_below_user = True
        exc = exc.__cause__
        typ = exc.__class__
    entries = []
    delete_in = None
    delete_from = None
    fragment_index = None
    fragment_value = None
    fragment_decorator = None
    fragment_debuginfo = None
    frame_kind = ''
    while tb is not None:
        filename, lineno, funcname, source = traceback.extract_tb(tb, limit=1)[0]
        frame_kind = 'normal'
        local = tb.tb_frame.f_locals
        lines = []

        # cut out this part
        if (tb.tb_frame.f_code is core.chain.run_to_exhaustion.__code__ or
                tb.tb_frame.f_code is core.chain.apply.__code__):
            delete_in = len(entries)

        # top level of a spy.fragment()
        if '_spy_fragment_index' in local:
            if delete_in is not None or delete_all:  # pragma: no branch
                del entries[0 if delete_all else delete_in:]
            delete_in = len(entries)
            fragment_index = local['_spy_fragment_index']
            if '_spy_value' in local:  # pragma: no branch
                fragment_value = (local['_spy_value'],)
            frame_kind = 'fragment'

        # decorator
        if '_spy_decorator' in local:
            if delete_in is not None:  # pragma: no branch
                del entries[delete_in:]
            delete_in = len(entries)
            fragment_decorator = local['_spy_decorator']
            if '_spy_callable' in local:  # pragma: no branch
                callable_ = local['_spy_callable']
                if hasattr(callable_, '_spy_debuginfo'):
                    fragment_debuginfo = callable_._spy_debuginfo
            frame_kind = 'decorator'
            filename, lineno, funcname, source = traceback.extract_tb(tb.tb_next, limit=1)[0]

        # the next frame is the fragment body
        if tb.tb_frame.f_code is core._call_fragment_body.__code__:
            if delete_in is not None:  # pragma: no branch
                del entries[delete_in:]
            delete_in = len(entries)
            frame_kind = 'callable'

        # cli make_callable
        if hasattr(local, '_spy_debuginfo'):
            if delete_in is not None:  # pragma: no branch
                del entries[delete_in:]
            fragment_debuginfo = local._spy_debuginfo
            frame_kind = 'synthetic_callable'
        elif fragment_debuginfo and isinstance(tb.tb_frame.f_globals, Context):
            if delete_in is not None:  # pragma: no branch
                del entries[delete_in:]
            frame_kind = 'synthetic_callable'

        if fragment_debuginfo:
            fragment_name = fragment_debuginfo[0]
        else:
            fragment_name = 'Fragment {}'.format(fragment_index)

        if frame_kind == 'fragment' or frame_kind == 'callable':
            lines.append('  ' + fragment_name)
        elif frame_kind == 'decorator':
            decname = getattr(fragment_decorator, '__qualname__', fragment_decorator.__name__)
            decmod = inspect.getmodule(fragment_decorator)
            if decmod:  # pragma: no branch
                decname = '{}.{}'.format(decmod.__name__, decname)
            lines.append('  {}, in decorator {}'.format(fragment_name, decname))
            if fragment_debuginfo:
                lines.append('    ' + fragment_debuginfo[1])
            hide_below_user = True
        elif frame_kind == 'synthetic_callable':
            lines.append('  ' + fragment_name)
            lines.append('    ' + fragment_debuginfo[1])
        if frame_kind != 'normal':
            if fragment_value:  # pragma: no branch
                lines.append('    input to fragment was {!r}'.format(fragment_value[0]))
            entries.append(list(l + '\n' for l in lines))
            delete_from = len(entries)
        else:
            entries.append(list(traceback.format_list([(filename, lineno, funcname, source)])))
        tb = tb.tb_next
    if hide_below_user and delete_from is not None:
        del entries[delete_from:]
    entries.append(traceback.format_exception_only(typ, exc))
    entries.insert(0, ['Traceback (most recent call last):\n'])
    return entries


def _print(entries):
    print(''.join(itertools.chain.from_iterable(entries)), end='', file=sys.stderr)


_old_excepthook = sys.__excepthook__


def _excepthook(typ, exc, tb):
    if isinstance(exc, CaughtException):
        exc.print_traceback()
    else:
        _old_excepthook(typ, exc, tb)


def _install_excepthook():
    global _old_excepthook
    if sys.excepthook is _excepthook:
        return
    _old_excepthook = sys.excepthook
    sys.excepthook = _excepthook


class handler:
    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        _install_excepthook()

    def __exit__(self, typ, exc, traceback):
        if exc is None:
            return
        formatted = _format_exc(typ, exc, traceback, **self.kw)
        raise CaughtException(formatted) from exc
