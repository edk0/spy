import builtins
import functools
import importlib
import itertools
import sys

from clize import Clize, run
from clize.errors import MissingValue, UnknownOption
from clize.parser import Parameter, NamedParameter

from . import catcher, fragments
from .decorators import decorators
from .objects import Context, SpyFile, _ContextInjector

import spy


PIPE_NAME = 'pipe'


class NullContext:
    def __enter__(self):
        pass
    def __exit__(self, typ, value, traceback):
        pass


def compile_(code, filename='<input>'):
    try:
        return compile(code, filename, 'eval', 0, True, 0), True
    except SyntaxError:
        return compile(code, filename, 'exec', 0, True, 0), False


def make_callable(code, is_expr, env, pipe_name, debuginfo=(None, None)):
    local = env.view()
    local._spy_debuginfo = debuginfo
    proxy = local.overlay['spy'] = _ContextInjector(spy)
    if is_expr:
        def fragment_fn(value, context=None):
            local.overlay[pipe_name] = value
            proxy._ContextInjector__context = context
            return eval(code, env, local)
    else:
        def fragment_fn(value, context=None):
            local.overlay[pipe_name] = value
            proxy._ContextInjector__context = context
            eval(code, env, local)
            return local[pipe_name]
    fragment_fn._spy_debuginfo = debuginfo
    return fragment_fn


def make_context():
    context = Context()
    context.update(builtins.__dict__)
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
        try:
            if arg[0:2] == '--':
                return [ba.sig.aliases[arg]]
            elif arg[0] == '-':
                return [ba.sig.aliases['-' + c] for c in arg[1:]]
            else:
                return arg
        except KeyError as e:
            raise UnknownOption(e.args[0])

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

    pipe_name = sys.intern(pipe_name)

    spy.context = context = make_context()

    step_src = steps
    steps = []
    for i, code in enumerate(step_src):
        fragment_name = 'Fragment {}'.format(i + 1)
        source = code
        if isinstance(code, _Decorated):
            source = '{} {!r}'.format(code.name, code.value)
            code, funcseq = code.value, code.funcseq
        else:
            funcseq = ()
        co, is_expr = compile_(code, filename=fragment_name)
        debuginfo = (fragment_name, source)
        ca = make_callable(co, is_expr, context, pipe_name, debuginfo)
        for fn in funcseq:
            try:
                ca = fn(ca, debuginfo=debuginfo)
            except TypeError:
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
        context = NullContext()
    else:
        context = catcher.handler(delete_all=True)

    with context:
        chain.run_to_exhaustion(data)

_main = Clize(_main, extra=tuple(Decorator(aliases=fn.decorator_names,
                                           description=fn.decorator_help,
                                           decfn=fn)
                                 for fn in decorators))

def main():
    run(_main)
