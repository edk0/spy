import io
import subprocess
import sys

import pytest

import spy.cli
from spy.objects import Context


class TestCompile:
    def test_expr(self):
        code, is_expr = spy.cli.compile_('3 + 4')
        assert is_expr
        assert eval(code) == 7

    def test_exec(self):
        code, is_expr = spy.cli.compile_('x = True')
        assert not is_expr

        scope = {}
        eval(code, scope, scope)
        assert scope.get('x') is True


def test_make_callable():
    context = Context(_pipe_name='pipe')
    code, is_expr = spy.cli.compile_('x = pipe.upper(); pipe = x[::-1]')
    ca = spy.cli.make_callable(code, is_expr, context)
    assert ca('bar') == 'RAB'


def test_get_imports():
    co, is_expr = spy.cli.compile_('abc.defg(foo.bar)')
    assert set(spy.cli.get_imports(co)) >= {'abc', 'foo', 'foo.bar'}


def test_make_context():
    context = spy.cli.make_context(['collections', 'i am pretty sure this module does not exist'])
    assert 'collections' in context


def test_context_builtins():
    context = spy.cli.make_context()
    # inner scope won't have builtins unless context does
    eval('[int(x) for x in (1, 2)]', context, context)


def test_excepthook(capsys):
    try:
        spy.cli._main(sys.argv[0], '-f', 'this_name_does_not_exist_either')
    except SystemExit:
        out, err = capsys.readouterr()
        for line in err.splitlines():
            assert "spy/main.py" not in line
        assert "  Fragment 1" in err.splitlines()
        assert "    --filter 'this_name_does_not_exist_either'" in err.splitlines()

    with pytest.raises(NameError):
        spy.cli._main(sys.argv[0], '--no-exception-handling', 'still_broken_i_hope')


def test_run(capsys):
    input = "this is\na piece of sample input\nused to test a complete run"
    expected = "SAMPLE PIECE THIS\nTEST USED INPUT\nRUN COMPLETE\n"
    stdin = sys.stdin
    argv = sys.argv
    try:
        sys.stdin = io.StringIO(input)
        sys.argv = sys.argv[0:1] + [
                '-l',
                'spy.many(pipe.split())',
                '-f', 'len(pipe) > 2',
                'pipe.upper()',
                'list(itertools.islice(spy.collect(), 3))',
                '" ".join(reversed(pipe))']
        with pytest.raises(SystemExit):
            from spy import __main__
        out, err = capsys.readouterr()
        assert out == expected
    finally:
        sys.stdin = stdin
        sys.argv = argv
