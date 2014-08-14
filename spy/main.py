import builtins
import importlib
import itertools
import sys

from clize import Clize, run
from clize.parser import Parameter, NamedParameter

import dis
if not hasattr(dis, 'get_instructions'):
    from . import dis34 as dis

from . import fragments
from .decorators import decorators
from .objects import Context, SpyFile

import spy


PIPE_NAME = 'pipe'


def compile_(code, filename='<input>'):
    try:
        return compile(code, filename, 'eval', 0, True, 0), True
    except SyntaxError:
        return compile(code, filename, 'exec', 0, True, 0), False


def make_callable(code, is_expr, context):
    def fragment_fn(value):
        local = context.pipe_view(value)
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


class _Decorated:
    def __init__(self, f, v):
        self.funcseq = f
        self.value = v


class Decorator(NamedParameter):
    def __init__(self, *a, decfn, **kw):
        super().__init__(*a, **kw)
        self.decfn = decfn

    def read_argument(self, ba, i):
        ba.skip = 1
        ba.args.append(_Decorated((self.decfn,), ba.in_args[i + 1]))


def _main(*steps,
         each_line: 'l' = False,
         start: (int, 's') = 0,
         end: (int, 'e') = None,
         no_default_fragments = False):
    """Run Python code.

    steps: At least one Python expression (or suite) to execute

    each_line: If specified, process lines as strings rather than all of stdin as a file

    start: Don't print before this result (zero-based)

    end: Stop after getting this result (zero-based)
    """
    compiled_steps = []
    imports = set()
    for code in steps:
        if isinstance(code, _Decorated):
            code, funcseq = code.value, code.funcseq
        else:
            funcseq = ()
        co, is_expr = compile_(code, filename=code)
        imports |= set(get_imports(co))
        compiled_steps.append((co, is_expr, funcseq))

    context = make_context(imports)
    spy.context = context

    steps = []
    for co, is_expr, funcseq in compiled_steps:
        ca = make_callable(co, is_expr, context)
        for fn in funcseq:
            ca = fn(ca)
        steps.append(spy.step(ca))

    if not no_default_fragments:
        steps.insert(0, fragments.init)
        steps.append(fragments.make_limit(start=start, end=end))
        steps.append(fragments.print)

        if each_line:
            steps.insert(1, fragments.many)

    for item in spy.chain(steps):
        pass

_main = Clize(_main, extra=tuple(Decorator(aliases=fn.decorator_names, decfn=fn) for fn in decorators))

def main():
    run(_main)

