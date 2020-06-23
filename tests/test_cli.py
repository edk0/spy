import io
import subprocess
import sys

import clize.errors

import pytest

import spy
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
    context = Context()
    code, is_expr = spy.cli.compile_('x = pipe.upper(); pipe = x[::-1]')
    ca = spy.cli.make_callable(code, is_expr, context, 'pipe')
    assert ca('bar') == 'RAB'


def test_context_builtins():
    context = spy.cli.make_context()
    # inner scope won't have builtins unless context does
    eval('[int(x) for x in (1, 2)]', context, context)


def test_argument_errors(monkeypatch):
    test_inputs = [
        ['-a'],
        ['-a', '-a'],
        ['-a', '-l'],
        ['-a', '--accumulate'],
        ['--accumulate'],
        ['--accumulate', '-a'],
        ['-l', '-a']
    ]
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    for input_ in test_inputs:
        try:
            spy.cli._cli()(sys.argv[0], *input_)
        except ValueError as e:
            assert 'No value found after --accumulate' in str(e)


def test_argument_chain(monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    spy.cli._cli()(sys.argv[0], '1+', '2+', '3')
    with pytest.raises(SystemExit):
        spy.cli._cli()(sys.argv[0], '1+', '2+')


def test_syntax_error(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    with pytest.raises(SystemExit):
        spy.cli._cli()(sys.argv[0], 'x = * 1')
    out, err = capsys.readouterr()
    lines = iter(err.splitlines())
    for line in lines:
        if 'x = * 1' in line:
            pointer = next(lines)
            break
    else:
        assert False, "missing error source output"
    assert line.find('*') == pointer.find('^')

    with pytest.raises(SystemExit):
        spy.cli._cli()(sys.argv[0], 'pass\nx = * 1')
    out, err = capsys.readouterr()
    lines = iter(err.splitlines())
    for line in lines:
        if 'x = * 1' in line:
            pointer = next(lines)
            break
    else:
        assert False, "missing error source output"
    assert line.find('*') == pointer.find('^')


def test_prelude(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    spy.cli._cli()(sys.argv[0], '--prelude', 'x = 123', 'x')
    out, err = capsys.readouterr()
    assert out.strip() == '123'


def test_unknown_option(monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    try:
        spy.cli._cli()(sys.argv[0], '-a!')
    except ValueError as e:
        assert 'Unknown option' in str(e)


def test_excepthook(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    try:
        spy.cli._cli()(sys.argv[0], '-f', 'this_name_does_not_exist_either')
        pytest.fail("didn't raise an exception")
    except Exception:
        sys.excepthook(*sys.exc_info())
    out, err = capsys.readouterr()
    for line in err.splitlines():
        assert "spy/main.py" not in line
    assert "  Fragment 1" in err.splitlines()
    assert "    --filter 'this_name_does_not_exist_either'" in err.splitlines()
    with pytest.raises(NameError):
        spy.cli._cli()(sys.argv[0], '--no-exception-handling', 'still_broken_i_hope')


def test_decorator_exceptions(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    try:
        spy.cli._cli()(sys.argv[0], '-c', 'a_b_c_d_e_f')
        pytest.fail("didn't raise an exception")
    except Exception:
        sys.excepthook(*sys.exc_info())
    out, err = capsys.readouterr()
    assert 'a_b_c_d_e_f' in err

    try:
        spy.cli._cli()(sys.argv[0], '-k', 'u_v_w_x_y_z')
        pytest.fail("didn't raise an exception")
    except Exception:
        sys.excepthook(*sys.exc_info())
    out, err = capsys.readouterr()
    assert 'u_v_w_x_y_z' in err


def test_collect_context(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    try:
        spy.cli._cli()(sys.argv[0], 'spy.collect(context=None)')
        pytest.fail("didn't raise an exception")
    except Exception:
        sys.excepthook(*sys.exc_info())
    out, err = capsys.readouterr()
    for line in err.splitlines():
        assert "spy/main.py" not in line
    assert "  Fragment 1" in err.splitlines()
    assert "ValueError: Can't collect without a valid context (got None)" in err.splitlines()


def test_run(capsys, monkeypatch):
    input = "this is\na piece of sample input\nused to test a complete run"
    expected = "SAMPLE PIECE THIS\nTEST USED INPUT\nRUN COMPLETE\n"
    monkeypatch.setattr(sys, 'stdin', io.StringIO(input))
    monkeypatch.setattr(sys, 'argv',
        sys.argv[0:1] + [
            '-l',
            'spy.many(pipe.split())',
            '-f', 'len(pipe) > 2',
            'pipe.upper()',
            'list(itertools.islice(spy.collect(), 3))',
            '" ".join(reversed(pipe))'])
    spy._dont_load_plugins = True
    with pytest.raises(SystemExit):
        from spy import __main__
    out, err = capsys.readouterr()
    assert err == ''
    assert out == expected


def test_raw(capsys, monkeypatch):
    input = "this is a string\nwhich i expect\0to get back exactly\v\r\nas it was put in"
    monkeypatch.setattr(sys, 'stdin', io.StringIO(input))
    monkeypatch.setattr(sys, 'argv',
        sys.argv[0:1] + ['--raw', '--each-line', '-c', 'sys.stdout.write', 'None'])
    spy._dont_load_plugins = True
    with pytest.raises(SystemExit):
        from spy import __main__
    out, err = capsys.readouterr()
    assert err == ''
    assert out == input


def test_no_defaults(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    monkeypatch.setattr(sys, 'argv',
        sys.argv[0:1] + [
            '--no-default-fragments',
            '"abcdef"',
            '--callable', 'print'])
    spy._dont_load_plugins = True
    with pytest.raises(SystemExit):
        from spy import __main__
    out, err = capsys.readouterr()
    assert err == ''
    assert out == 'abcdef\n'


def test_show_fragments(capsys, monkeypatch):
    expected = '''
  1 | --filter --callable 'int'
  2 | --accumulate --accumulate 'asdfgfa'
  3 | --many 'test'
  4 | --many --many 'baz'
'''
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    argv = sys.argv[0:1] + [
            '--show-fragments',
            '-l',
            '-fc', 'int',
            '--accumulate', '-a', 'asdfgfa',
            '-m', 'test',
            '-m', '--many', 'baz']
    spy.cli._cli()(*argv)
    out, err = capsys.readouterr()
    assert expected in out


def test_literal(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    argv = sys.argv[0:1] + [
            '--no-exception-handling',
            '"foo"',
            '-fi', '{1}']
    spy.cli._cli()(*argv)
    out, err = capsys.readouterr()
    assert out == 'foo\n'
    assert not err

    argv = sys.argv[0:1] + [
            '--no-exception-handling',
            '-m', '"foo"',
            '-ia', '{0} {1} {2}']
    with pytest.raises(clize.errors.MissingValue):
        spy.cli._cli()(*argv)


def test_literal_and_autojoin(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    argv = sys.argv[0:1] + [
            '--no-exception-handling',
            '-i', '1+',
            '2']
    spy.cli._cli()(*argv)
    out, err = capsys.readouterr()
    assert out == '2\n'
    assert not err


def test_setenv(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    argv = sys.argv[0:1] + [
            '--no-exception-handling',
            '{"foo": "bar"}',
            '-ki', '{foo}']
    spy.cli._cli()(*argv)
    out, err = capsys.readouterr()
    assert out == 'bar\n'
    assert not err

    argv = sys.argv[0:1] + [
            '--no-exception-handling',
            '{"foo": "bar"}',
            '-k', 'foo']
    spy.cli._cli()(*argv)
    out, err = capsys.readouterr()
    assert out == 'bar\n'
    assert not err
