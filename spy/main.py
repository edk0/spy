import builtins
import dis
import importlib
import sys

from collections.abc import Iterable, Mapping
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


def pretty_print(thing, expand_iterables=True, limit=None):
    if isinstance(thing, str):
        print(thing)
        return 1
    elif expand_iterables and isinstance(thing, Iterable) and not isinstance(thing, Mapping):
        count = 0
        for element in thing:
            if limit is not None and count >= limit:
                return count + 1
            count += pretty_print(element, False)
        return count
    elif thing is None:
        return 0
    else:
        sys.displayhook(thing)
        return 1


def _main(*steps: Parameter.REQUIRED,
         each_line: 'l' = False,
         start: (int, 's') = 0,
         end: (int, 'e') = None):
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
        def step(ita, context, code=code, co=co, is_expr=is_expr):
            for item in ita:
                context[spy.PIPE_NAME] = item
                spy._iteration_state = (item, ita)
                result = eval(co, context)
                result = result if is_expr else context[spy.PIPE_NAME]
                try:
                    del context[spy.PIPE_NAME]
                except KeyError:
                    pass
                if result is spy.DROP:
                    continue
                elif isinstance(result, spy.many):
                    yield from result
                else:
                    yield result
        step.__name__ = code
        compiled_steps.append(step)

    context = make_context(imports)
    spy.context = context

    compiled_steps.append(fragments.make_limit(start=start, end=end))
    compiled_steps.append(fragments.print)

    if each_line:
        compiled_steps.insert(0, fragments.many)

    initial = (SpyFile(sys.stdin),)
    ita = initial
    for cs in compiled_steps:
        ita = cs(ita, context)

    for item in ita:
        pass

def main():
    run(_main)

