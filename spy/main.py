import builtins
import importlib
import itertools
import sys
import traceback

from clize import Clize, run
from clize.parser import Parameter, NamedParameter

import dis
if not hasattr(dis, 'get_instructions'):
    from . import dis34 as dis

from . import fragments
from .decorators import decorators
from .objects import Context, _ContextView, SpyFile

import spy


PIPE_NAME = 'pipe'


def compile_(code, filename='<input>'):
    try:
        return compile(code, filename, 'eval', 0, True, 0), True
    except SyntaxError:
        return compile(code, filename, 'exec', 0, True, 0), False


def make_callable(code, is_expr, context, debuginfo=(None, None)):
    def fragment_fn(value):
        local = context.pipe_view(value)
        local._debuginfo = debuginfo + (value,)
        result = eval(code, context, local)
        return result if is_expr else local.value
    return fragment_fn


def get_imports(code):
    imp = []
    instrs = dis.get_instructions(code)
    for instr in instrs:
        if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
            name = code.co_names[instr.arg]
            imp.append(name)
            for instr_ in instrs:
                if instr_.opname == 'LOAD_ATTR':
                    name += '.' + code.co_names[instr_.arg]
                    imp.append(name)
                elif instr_.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                    name = code.co_names[instr_.arg]
                    imp.append(name)
                else:
                    break
    return imp


def make_context(imports=[], pipe_name=PIPE_NAME):
    context = Context(_pipe_name=pipe_name)
    for imp in imports:
        try:
            m = importlib.import_module(imp)
        except ImportError:
            continue
        if '.' not in imp:
            context[imp] = m
    return context


def excepthook(typ, value, tb):
    print('Traceback (most recent call last):', file=sys.stderr)
    entries = []
    while tb is not None:
        filename, lineno, funcname, source = traceback.extract_tb(tb, limit=1)[0]
        local = tb.tb_frame.f_locals
        debuginfo = getattr(local, '_debuginfo', None) or local.get('_spy_debuginfo', None)
        if debuginfo is not None:
            del entries[:]
            if hasattr(local, '_debuginfo'):
                format = '  {funcname}, line {lineno}\n'
            else:
                # line is meaningless, exception didn't take place during  the execution
                # of the fragment
                format = '  {funcname}\n'
            funcname, source, pipe_value = debuginfo
            entries.append(format.format(**locals()))
            entries.append('    {}\n'.format(source))
            entries.append('    input to fragment was {!r}\n'.format(pipe_value))
        else:
            entries.extend(traceback.format_list([(filename, lineno, funcname, source)]))
        tb = tb.tb_next
    entries.extend(traceback.format_exception_only(typ, value))
    print(''.join(entries), end='', file=sys.stderr)


class _Decorated:
    def __init__(self, f, v, name):
        self.funcseq = f
        self.value = v
        self.name = name


class Decorator(NamedParameter):
    def __init__(self, *a, decfn, **kw):
        super().__init__(*a, **kw)
        self.decfn = decfn

    def read_argument(self, ba, i):
        ba.skip = 1
        ba.args.append(_Decorated((self.decfn,), ba.in_args[i + 1], self.display_name))


def _main(*steps,
         each_line: 'l' = False,
         start: (int, 's') = 0,
         end: (int, 'e') = None,
         no_default_fragments = False,
         no_exception_handling = False):
    """Run Python code.

    steps: At least one Python expression (or suite) to execute

    each_line: If specified, process lines as strings rather than all of stdin as a file

    start: Don't print before this result (zero-based)

    end: Stop after getting this result (zero-based)
    """
    compiled_steps = []
    imports = set()
    for i, code in enumerate(steps):
        fragment_name = 'Fragment {}'.format(i + 1)
        source = code
        if isinstance(code, _Decorated):
            source = '{} {!r}'.format(code.name, code.value)
            code, funcseq = code.value, code.funcseq
        else:
            funcseq = ()
        co, is_expr = compile_(code, filename=fragment_name)
        imports |= set(get_imports(co))
        compiled_steps.append((co, is_expr, funcseq, (fragment_name, source)))

    context = make_context(imports)
    spy.context = context

    steps = []
    for co, is_expr, funcseq, debuginfo in compiled_steps:
        ca = make_callable(co, is_expr, context, debuginfo)
        for fn in funcseq:
            try:
                ca = fn(ca, debuginfo=debuginfo)
            except:
                ca = fn(ca)
        steps.append(spy.step(ca))

    if not no_default_fragments:
        steps.insert(0, fragments.init)
        steps.append(fragments.make_limit(start=start, end=end))
        steps.append(fragments.print)

        if each_line:
            steps.insert(1, fragments.many)

    if not no_exception_handling:
        sys.excepthook = excepthook

    for item in spy.chain(steps):
        pass

_main = Clize(_main, extra=tuple(Decorator(aliases=fn.decorator_names, decfn=fn) for fn in decorators))

def main():
    run(_main)

