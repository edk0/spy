import builtins
import dis
import importlib
import itertools
import sys

from clize import Parameter, run

from . import fragments
from .objects import Context, SpyFile

import spy


PIPE_NAME = 'pipe'


def compile_(code, filename='<input>'):
    try:
        return compile(code, filename, 'eval', 0, True, 0), True
    except SyntaxError:
        return compile(code, filename, 'exec', 0, True, 0), False


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


def make_context(imports=[]):
    context = Context()
    for imp in imports:
        try:
            m = importlib.import_module(imp)
        except ImportError:
            continue
        if '.' not in imp:
            context[imp] = m
    return context


def _main(*steps: Parameter.REQUIRED,
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
        co, is_expr = compile_(code)
        imports |= set(get_imports(co))
        def step(ita, context, co=co, is_expr=is_expr):
            for item in ita:
                local = context.pipe_view(item)
                spy._iteration_state.append((item, ita))
                result = eval(co, context, local)
                spy._iteration_state.pop()
                result = result if is_expr else local.value
                if result is spy.DROP:
                    continue
                elif isinstance(result, spy.many):
                    yield from result
                else:
                    yield result
        compiled_steps.append(step)

    context = make_context(imports)
    spy.context = context

    if not no_default_fragments:
        compiled_steps.insert(0, fragments.init)
        compiled_steps.append(fragments.make_limit(start=start, end=end))
        compiled_steps.append(fragments.print)

        if each_line:
            compiled_steps.insert(1, fragments.many)

    initial = itertools.repeat(None)
    ita = initial
    for cs in compiled_steps:
        ita = cs(ita, context)

    for item in ita:
        pass

def main():
    run(_main)

