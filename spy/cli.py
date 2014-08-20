import builtins
import functools
import importlib
import itertools
import sys

from clize import Clize, run
from clize.errors import ArgumentError, MissingValue
from clize.parser import Parameter, NamedParameter

import dis
if not hasattr(dis, 'get_instructions'):
    from . import dis34 as dis

from . import catcher, fragments
from .decorators import decorators
from .objects import Context, SpyFile

import spy


PIPE_NAME = 'pipe'


class _ModuleProxy:
    def __init__(self, module):
        self._module = module
        self._context = None

    def __getattr__(self, k):
        v = getattr(self._module, k)
        if getattr(v, '_spy_inject_context', None) is True:
            @functools.wraps(v)
            def wrapper(*a, **kw):
                if 'context' not in kw:
                    kw['context'] = self._context
                return v(*a, **kw)
            return wrapper
        else:
            return v


def compile_(code, filename='<input>'):
    try:
        return compile(code, filename, 'eval', 0, True, 0), True
    except SyntaxError:
        return compile(code, filename, 'exec', 0, True, 0), False


def make_callable(code, is_expr, env, debuginfo=(None, None)):
    local = env.pipe_view(None)
    local._spy_debuginfo = debuginfo
    proxy = _ModuleProxy(spy)
    local.overlay['spy'] = proxy
    if is_expr:
        def fragment_fn(value, context=None):
            local.value = value
            proxy._context = context
            return eval(code, env, local)
    else:
        def fragment_fn(value, context=None):
            local.value = value
            proxy._context = context
            eval(code, env, local)
            return local.value
    fragment_fn._spy_debuginfo = debuginfo
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
    context.update(builtins.__dict__)
    for imp in imports:
        try:
            m = importlib.import_module(imp)
        except (ImportError, OSError):
            continue
        if '.' not in imp:
            context[imp] = m
    return context


class _Decorated:
    def __init__(self, f, v, name):
        self.funcseq = f
        self.value = v
        self.name = name


class Decorator(NamedParameter):
    def __init__(self, *a, description, decfn, **kw):
        super().__init__(*a, **kw)
        self.description = description
        self.decfn = decfn

    def parse_one_arg(self, ba, arg):
        if arg[0:2] == '--':
            return [ba.sig.aliases[arg]]
        elif arg[0] == '-':
            return [ba.sig.aliases['-' + c] for c in arg[1:]]
        else:
            return arg

    def read_argument(self, ba, i):
        src = None
        io = i
        funcseq = [self.decfn]
        names = [self.display_name]
        arg = ba.in_args[i]
        if arg[1] == '-':
            i += 1
            try:
                arg = ba.in_args[i]
            except:
                raise MissingValue
        else:
            if len(arg) >= 3:
                arg = '-' + arg[2:]
            else:
                i += 1
                try:
                    arg = ba.in_args[i]
                except:
                    raise MissingValue
        while True:
            narg = self.parse_one_arg(ba, arg)
            if isinstance(narg, list):
                for dec in narg:
                    if not isinstance(dec, Decorator):
                        raise MissingValue
                    funcseq.append(dec.decfn)
                    names.append(dec.display_name)
            elif isinstance(narg, str):
                src = narg
                break
            i += 1
            if i >= len(ba.in_args):
                raise MissingValue
            arg = ba.in_args[i]
        ba.skip = i - io
        funcseq.reverse()
        ba.args.append(_Decorated(funcseq, src, ' '.join(names)))


def _main(*steps,
         each_line: 'l' = False,
         start: (int, 's') = 0,
         end: (int, 'e') = None,
         pipe_name: Parameter.UNDOCUMENTED = PIPE_NAME,
         no_default_fragments: Parameter.UNDOCUMENTED = False,
         no_exception_handling: Parameter.UNDOCUMENTED = False,
         show_fragments: Parameter.UNDOCUMENTED = False):
    """Run Python code.

    steps: At least one Python expression (or suite) to execute

    each_line: If specified, process lines as strings rather than all of stdin as a file

    start: Don't print before this result (zero-based)

    end: Stop after getting this result (zero-based)
    """
    sys.setcheckinterval(10000)

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

    context = make_context(imports, pipe_name=pipe_name)
    spy.context = context

    steps = []
    for co, is_expr, funcseq, debuginfo in compiled_steps:
        ca = make_callable(co, is_expr, context, debuginfo)
        for fn in funcseq:
            try:
                ca = fn(ca, debuginfo=debuginfo)
            except:
                ca = fn(ca)
        steps.append(spy.fragment(ca))

    index_offset = 0

    if not no_default_fragments:
        steps.append(fragments.make_limit(start=start, end=end))
        steps.append(fragments.print)

        if each_line:
            steps.insert(0, fragments.many)
            index_offset -= 1

    chain = spy.chain(steps, index_offset=index_offset)
    data = [SpyFile(sys.stdin)]

    if show_fragments:
        print(chain.format())
        return

    if no_exception_handling:
        chain.run_to_exhaustion(data)
    else:
        with catcher.handler(delete_all=True):
            chain.run_to_exhaustion(data)

_main = Clize(_main, extra=tuple(Decorator(aliases=fn.decorator_names,
                                           description=fn.decorator_help,
                                           decfn=fn)
                                 for fn in decorators))

def main():
    run(_main)

