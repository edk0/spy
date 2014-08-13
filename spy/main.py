import builtins
import dis
import importlib
import sys

from collections.abc import Iterable, Mapping
from clize import Parameter, run

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
         stream: 's' = False,
         prefilter: (str, 'b') = None,
         postfilter: (str, 'a') = None,
         limit: (int, 'l') = None):
    """Run Python code.

    code: Python to run

    stream: If specified, process lines as strings rather than all of stdin as a file

    limit: Limit number of results displayed
    """
    compiled_steps = []
    imports = set()
    for code in steps:
        co, is_expr = compile_(code)
        imports |= set(get_imports(co))
        def step(context, co=co, is_expr=is_expr):
            result = eval(co, context)
            return result if is_expr else context[PIPE_NAME]
        compiled_steps.append(step)

    context = make_context(imports)
    spy.context = context

    def process(values, steps, expand_iterables, limit=None):
        nonlocal context
        count = 0
        for v in values:
            if limit is not None and count >= limit:
                return count + 1
            for n, step in enumerate(steps):
                context[PIPE_NAME] = v
                v = step(context)
                if v is spy.DROP:
                    break
                elif isinstance(v, spy.many):
                    limit_ = None if limit is None else limit - count
                    count += process(v.ita, steps[n + 1:], False, limit_)
                    v = spy.DROP
                    break
            if v is not spy.DROP:
                limit_ = None if limit is None else limit - count
                count += pretty_print(v, expand_iterables, limit_)
        return count

    if stream:
        def stream_step(context):
            return spy.many(context[PIPE_NAME])
        compiled_steps.insert(0, stream_step)

    initial = (SpyFile(sys.stdin),)
    count = process(initial, compiled_steps, True, limit)

    if limit is not None and count > limit:
        print('...')

def main():
    run(_main)

