import builtins
import sys

from clize import Clize, run
from clize.errors import MissingValue, UnknownOption
from clize.parameters import multi
from clize.parser import use_mixin, Parameter, NamedParameter

from . import catcher, fragments
from .decorators import decorators
from .objects import Context, _ContextInjector

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
        try:
            return compile(code, filename, 'exec', 0, True, 0), False
        except Exception as e:
            raise e from None


def make_callable(code, is_expr, env, pipe_name, debuginfo=(None, None)):
    local = env.view()
    local._spy_debuginfo = debuginfo
    overlay = local.overlay
    proxy = overlay['spy'] = _ContextInjector(spy)
    if is_expr:
        def fragment_fn(value, context=None):
            overlay[pipe_name] = value
            proxy._ContextInjector__context = context
            return eval(code, env, local)
    else:
        def fragment_fn(value, context=None):
            overlay[pipe_name] = value
            proxy._ContextInjector__context = context
            eval(code, env, local)
            return local[pipe_name]
    fragment_fn._spy_debuginfo = debuginfo
    return fragment_fn


def make_context():
    context = Context()
    context.update(builtins.__dict__)
    return context


class StepList:
    @staticmethod
    def _read(ba, i):
        arg = ba.in_args[i]
        while True:
            try:
                compile_(arg, 'test')
                break
            except SyntaxError:
                i += 1
                if i >= len(ba.in_args):
                    break
                arg += ' ' + ba.in_args[i]
        return i, arg

    def read_argument(self, ba, i):
        io = i
        i, arg = self._read(ba, i)
        ba.skip = i - io
        ba.args.append(arg)


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

    def prepare_help(self, helper):
        helper.sections.setdefault("Decorators", {})
        helper.sections["Decorators"][self.display_name] = (self, '')
        del helper.sections["Options"][self.display_name]

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
            except LookupError:
                raise MissingValue
        else:
            if len(arg) >= 3:
                arg = '-' + arg[2:]
            else:
                i += 1
                try:
                    arg = ba.in_args[i]
                except LookupError:
                    raise MissingValue
        while True:
            narg = self.parse_one_arg(ba, arg)
            if isinstance(narg, list):
                for dec in narg:
                    if not isinstance(dec, Decorator):
                        raise MissingValue
                    funcseq.append(dec.decfn)
                    names.append(dec.display_name)
            else:
                i, src = StepList._read(ba, i)
                break
            i += 1
            if i >= len(ba.in_args):
                raise MissingValue
            arg = ba.in_args[i]
        ba.skip = i - io
        funcseq.reverse()
        ba.args.append(_Decorated(funcseq, src, ' '.join(names)))


def _main(*steps: use_mixin(StepList),
          each_line: 'l' = False,
          start: (int, 's') = 0,
          end: (int, 'e') = None,
          prelude: (multi(), 'n') = '',
          pipe_name: Parameter.UNDOCUMENTED = PIPE_NAME,
          no_default_fragments: Parameter.UNDOCUMENTED = False,
          no_exception_handling: Parameter.UNDOCUMENTED = False,
          show_fragments: Parameter.UNDOCUMENTED = False):
    """Run Python code.

    :param steps: At least one Python expression (or suite) to execute
    :param each_line: If specified, process lines as strings rather than all of stdin as a file
    :param start: Don't print before this result (zero-based)
    :param end: Stop after getting this result (zero-based)
    :param prelude: Execute this statement before running any steps
    """
    sys.setcheckinterval(10000)

    pipe_name = sys.intern(pipe_name)

    spy.context = context = make_context()

    for stmt in prelude:
        exec(stmt, context, context.view())

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

        steps.insert(0, fragments.stdin)
        index_offset -= 1

    chain = spy.chain(steps, index_offset=index_offset)
    data = [None]

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
