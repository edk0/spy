import builtins
import platform
import sys
from contextlib import ExitStack
from functools import partial
from itertools import chain

from clize import Clize, run
from clize.errors import ArgumentError, MissingValue, UnknownOption, SetArgumentErrorContext
from clize.parameters import multi
from clize.parser import use_mixin, Parameter, NamedParameter
from pkg_resources import iter_entry_points

from . import catcher, fragments, prelude
from .decorators import decorators
from .objects import Context, _ContextInjector

import spy


PIPE_NAME = 'pipe'


class DebuggerContext:  # pragma: no cover
    def __enter__(self):
        pass

    def __exit__(self, typ, value, traceback):
        if traceback is not None:
            debugger(traceback)


def debugger(tb=None):  # pragma: no cover
    try:
        import bpdb
        bpdb.post_mortem(tb)
    except ImportError:
        import pdb
        pdb.post_mortem(tb)


def compile_(code, filename='<input>'):
    try:
        return compile(code, filename, 'eval', 0, True, 0), True
    except SyntaxError:
        pass
    return compile(code, filename, 'exec', 0, True, 0), False


def pretty_syntax_error(source, err):
    print('Error compiling %s' % err.filename, file=sys.stderr)
    for lineno, line in enumerate(source.splitlines(), start=1):
        print('  %s' % line, file=sys.stderr)
        if err.lineno == lineno and err.offset > 0:
            off = err.offset - 1
            if (err.text is None and sys.version_info < (3, 8)) or \
                    platform.python_implementation() == 'PyPy':  # pragma: no cover
                off += 1
            print('  %s^' % (' ' * off), file=sys.stderr)
    print('%s: %s' % (type(err).__name__, err.msg), file=sys.stderr)


def make_callable(code, is_expr, env, pipe_name, debuginfo=(None, None)):
    local = orig_local = env.view()
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
            return orig_local[pipe_name]
    def setenv(m):
        nonlocal env, local
        local = m
    fragment_fn._spy_debuginfo = debuginfo
    fragment_fn._spy_setenv = setenv
    return fragment_fn


def make_literal(code, env, pipe_name, debuginfo):
    local = env.view()
    local._spy_debuginfo = debuginfo
    def fragment_fn(value):
        local[pipe_name] = value
        return (local, code)
    def setenv(m):
        nonlocal env, local
        local = m
    fragment_fn._spy_debuginfo = debuginfo
    fragment_fn._spy_setenv = setenv
    return fragment_fn


def make_context():
    prelude_things = {k: getattr(prelude, k) for k in prelude.__all__}
    context = Context()
    context.update(builtins.__dict__)
    context.update(prelude_things)
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
    LITERAL = False

    def __init__(self, f, v, name):
        self.funcseq = f
        self.value = v
        self.name = name


class _LiteralDecorated(_Decorated):
    LITERAL = True


class Decorator(NamedParameter):
    LITERAL = False

    def __init__(self, *a, description, dec_args, decfn, **kw):
        super().__init__(*a, **kw)
        self.description = description
        self.dec_args = dec_args
        self.decfn = decfn
        self.marker_class = _Decorated

    def prepare_help(self, helper):
        helper.sections.setdefault("Decorators", {})
        helper.sections["Decorators"][self.display_name] = (self, '')
        del helper.sections["Options"][self.display_name]

    def format_argument(self, long_alias):
        if not self.dec_args:
            return ''
        return ('=' if long_alias else ' ') + ' '.join(
            conv.usage_name for conv in self.dec_args)

    def get_all_names(self):
        names = super().get_all_names()
        long_alias = any(alias.startswith('--') for alias in self.aliases)  # pragma: no branch
        return names + self.format_argument(long_alias)

    def parse_one_arg(self, ba, arg):
        try:
            if arg[0:2] == '--':
                arg, _, val = arg.partition('=')
                return [ba.sig.aliases[arg]], val
            elif arg[0] == '-':
                return [ba.sig.aliases['-' + c] for c in arg[1:]], None
            else:
                return arg, None
        except KeyError as e:
            raise UnknownOption(e.args[0])

    def coalesce(self, dec, decseq, funcseq, names):
        decseq.append(dec)
        funcseq.append(dec.decfn)
        names.append(dec.display_name)
        return dec.marker_class

    def read_argument(self, ba, i):
        with SetArgumentErrorContext(param=self):
            self._read_argument(ba, i)

    @staticmethod
    def arg_iterator(start):
        iterators = [iter(x) for x in start]
        def iterate():
            while iterators:
                while iterators:
                    try:
                        v = next(iterators[0])
                        yield v
                        break
                    except StopIteration:
                        iterators.pop(0)
        def pushback(x):
            iterators.insert(0, iter(x))
        return iterate(), pushback

    def _read_argument(self, ba, i):
        src = None
        io = i
        funcseq = [self.decfn]
        names = [self.display_name]
        arg = ba.in_args[i]
        decseq = [self]
        cls = self.marker_class
        stacked = -1
        eq = -1
        leader = []
        if arg[1] == '-':
            if '=' in arg[2:]:
                leader.append((i, arg[2:].split('=', 1)[1]))
                eq = i
            try:
                i += 1
                leader.append((i, ba.in_args[i]))
            except LookupError:
                raise MissingValue
        else:
            if len(arg) >= 3:
                leader.append((i, '-' + arg[2:]))
                stacked = i
            else:
                try:
                    i += 1
                    leader.append((i, ba.in_args[i]))
                except LookupError:
                    raise MissingValue
        ita, pushback = self.arg_iterator([leader, enumerate(ba.in_args[i + 1:], start=i + 1)])
        for i, arg in ita:
            if getattr(funcseq[-1], 'dec_args', None):
                with SetArgumentErrorContext(param=decseq[-1]):
                    # if this is a reconstructed next option, we must have
                    # left-composed a short option that takes args, which is
                    # definitely wrong
                    if i == stacked:
                        raise MissingValue
                    ita_ = chain(((i, arg),), ita)
                    da = self._read_dec_args(ita_, decseq[-1], names)
                    funcseq[-1] = funcseq[-1](*da)
                continue
            if i == eq:
                raise ArgumentError("{} does not take a value".format(
                    decseq[-1].display_name))
            narg, trail = self.parse_one_arg(ba, arg)
            if trail:
                pushback([(i, trail)])
                eq = i
            if isinstance(narg, list):
                for ind, dec in enumerate(narg):
                    with SetArgumentErrorContext(param=decseq[-1]):
                        if not isinstance(dec, Decorator):
                            raise MissingValue
                        if ind > 0 and decseq[-1].dec_args:
                            raise MissingValue
                        cls = decseq[-1].coalesce(dec, decseq, funcseq, names)
            elif not decseq[-1].LITERAL:
                i, src = StepList._read(ba, i)
                break
            else:
                src = ba.in_args[i]
                break
        else:
            raise MissingValue
        ba.skip = i - io
        funcseq.reverse()
        ba.args.append(cls(funcseq, src, ' '.join(names)))

    def _read_dec_args(self, ita, dec, names):
        a = []
        for elem, converter in zip(ita, dec.dec_args):
            i, arg = elem
            name = arg
            if not name.isdigit():
                name = repr(name)
            names.append(name)
            a.append(converter(arg))
            if len(a) >= len(dec.dec_args):
                break
        else:  # pragma: no cover
            raise MissingValue
        return a


class LiteralDecorator(Decorator):
    LITERAL = True

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.marker_class = _LiteralDecorated

    def coalesce(self, dec, decseq, funcseq, names):
        raise MissingValue


def _main(*steps: use_mixin(StepList),
          each_line: 'l' = False,  # noqa: F821
          raw: 'r' = False,  # noqa: F821
          start: (int, 's') = 0,  # noqa: F821
          end: (int, 'e') = None,  # noqa: F821
          prelude: (multi(), 'p') = 'pass',  # noqa: F821
          pipe_name: Parameter.UNDOCUMENTED = PIPE_NAME,
          no_default_fragments: Parameter.UNDOCUMENTED = False,
          no_exception_handling: Parameter.UNDOCUMENTED = False,
          show_fragments: Parameter.UNDOCUMENTED = False,
          break_: Parameter.UNDOCUMENTED = False):
    """Feed data through a sequence of Python expressions.

    :param steps: At least one Python expression (or suite) to execute
    :param each_line: If specified, process lines as strings rather than all of stdin as a file
    :param start: Don't print before this result (zero-based)
    :param end: Stop after getting this result (zero-based)
    :param prelude: Execute this statement before running any steps. Can be specified more than once.
    :param raw: Don't add helper functionality to stdin
    """
    pipe_name = sys.intern(pipe_name)

    spy.context = context = make_context()

    for stmt in prelude:
        exec(stmt, context, context.view())

    step_src = steps
    steps = []
    for i, code in enumerate(step_src):
        fragment_name = 'Fragment {}'.format(i + 1)
        source = code
        literal = False
        if isinstance(code, _Decorated):
            source = '{} {!r}'.format(code.name, code.value)
            literal = code.LITERAL
            code, funcseq = code.value, code.funcseq
        else:
            funcseq = ()
        debuginfo = (fragment_name, source)
        if literal:
            ca = make_literal(code, context, pipe_name, debuginfo)
        else:
            try:
                co, is_expr = compile_(code, filename=fragment_name)
            except SyntaxError as e:
                pretty_syntax_error(code, e)
                if break_:  # pragma: no cover
                    debugger()
                sys.exit(1)
            ca = make_callable(co, is_expr, context, pipe_name, debuginfo)
        for fn in funcseq:
            ca = fn(ca)
        steps.append(spy.fragment(ca))

    index_offset = 0

    if not no_default_fragments:
        steps.append(fragments.make_limit(start=start, end=end))
        steps.append(fragments.print)

        if each_line:
            steps.insert(0, fragments.foreach)
            index_offset -= 1

        if raw:
            steps.insert(0, fragments.raw_stdin)
        else:
            steps.insert(0, fragments.stdin)
        index_offset -= 1

    chain = spy.chain(steps, index_offset=index_offset)
    data = [None]

    if show_fragments:
        print(chain.format())
        return

    with ExitStack() as stack:
        if not no_exception_handling:
            stack.enter_context(catcher.handler(delete_all=True))
        if break_:  # pragma: no cover
            stack.enter_context(DebuggerContext())
        chain.run_to_exhaustion(data)


def _prepare_decorators():
    rv = []
    for fn in decorators:
        if fn.takes_string:
            cls = LiteralDecorator
        else:
            cls = Decorator
        rv.append(cls(aliases=fn.decorator_names,
                      description=fn.decorator_help,
                      decfn=fn,
                      dec_args=fn.dec_args))
    return tuple(rv)


def _cli():
    return Clize(_main, extra=_prepare_decorators())


def main():
    if not spy._dont_load_plugins:
        for entry_point in iter_entry_points('spy.init'):
            entry_point.load()()
    run(_cli())
