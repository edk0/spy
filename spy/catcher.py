import contextlib
import inspect
import itertools
import sys
import traceback

from . import core


def _hook(typ, exc, tb, *, delete_all=False):
    entries = []
    delete_in = None
    skip = 0
    fragment_index = None
    fragment_value = None
    fragment_decorator = None
    fragment_decorator_value = None
    fragment_debuginfo = None
    frame_kind = last_kind = ''
    while tb is not None:
        filename, lineno, funcname, source = traceback.extract_tb(tb, limit=1)[0]
        last_kind = frame_kind
        frame_kind = 'normal'
        local = tb.tb_frame.f_locals
        lines = []

        # cut out this part
        if tb.tb_frame.f_code == core.chain.run_to_exhaustion.__code__:
            delete_in = len(entries)

        # top level of a spy.fragment()
        if '_spy_fragment_index' in local:
            if delete_in is not None or delete_all:
                del entries[delete_in or 0:]
            delete_in = len(entries)
            if delete_all:
                delete_in -= 1
            fragment_index = local['_spy_fragment_index']
            if '_spy_value' in local:
                fragment_value = (local['_spy_value'],)
            frame_kind = 'fragment'

        # decorator
        if '_spy_decorator' in local:
            if delete_in is not None:
                del entries[delete_in:]
            delete_in = len(entries)
            fragment_decorator = local['_spy_decorator']
            if '_spy_value' in local:
                fragment_decorator_value = local['_spy_value']
            if '_spy_callable' in local:
                callable_ = local['_spy_callable']
                if hasattr(callable_, '_spy_debuginfo'):
                    fragment_debuginfo = callable_._spy_debuginfo
            frame_kind = 'decorator'
            filename, lineno, funcname, source = traceback.extract_tb(tb.tb_next, limit=1)[0]

        # cli make_callable
        if hasattr(local, '_spy_debuginfo'):
            if delete_in is not None:
                del entries[delete_in:]
            fragment_debuginfo = local._spy_debuginfo
            frame_kind = 'synthetic_callable'

        if frame_kind == 'fragment':
            lines.append('  Fragment {}'.format(fragment_index))
        elif frame_kind == 'decorator':
            decname = getattr(fragment_decorator, '__qualname__', fragment_decorator.__name__)
            decmod = inspect.getmodule(fragment_decorator)
            if decmod:
                decname = '{}.{}'.format(decmod.__name__, decname)
            lines.append('  Fragment {}, in decorator {}'.format(fragment_index, decname))
            if fragment_debuginfo:
                lines.append('    ' + fragment_debuginfo[1])
        elif frame_kind == 'synthetic_callable':
            lines.append('  Fragment {}'.format(fragment_index))
            lines.append('    ' + fragment_debuginfo[1])

        if frame_kind != 'normal':
            if fragment_value:
                lines.append('    input to fragment was {!r}'.format(fragment_value[0]))
            entries.append(list(l + '\n' for l in lines))
        else:
            entries.append(list(traceback.format_list([(filename, lineno, funcname, source)])))
        tb = tb.tb_next
    entries.append(traceback.format_exception_only(typ, exc))
    print('Traceback (most recent call last):', file=sys.stderr)
    print(''.join(itertools.chain.from_iterable(entries)), end='', file=sys.stderr)


def get_hook(**kw):
    def excepthook(*a):
        return _hook(*a, **kw)
    return excepthook


class handler:
    def __init__(self, exit=True, **kw):
        self.exit = exit
        self.kw = kw

    def __enter__(self):
        pass

    def __exit__(self, typ, exc, traceback):
        if exc is None:
            return
        _hook(typ, exc, traceback, **self.kw)
        if self.exit:
            raise SystemExit(1) from exc
        else:
            return True
