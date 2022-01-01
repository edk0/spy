import importlib
import io
import sys

import pytest

import spy
import spy.cli
from spy import prelude
from spy.decorators import decorator


def init_test_plugin():
    prelude.xyz = 'abc123'
    prelude.__all__ += ['xyz']

    @decorator('--_test_plugin_uppercase', doc='Make the result uppercase')
    def uppercase(fn, v, context):
        return str(fn(v, context)).upper()


def iter_modules(*a, **kw):
    yield None, 'spy_test_plugin', True


_import_module = importlib.import_module
def import_module(name):
    if name == 'spy_test_plugin':
        sys.modules['spy_test_plugin'] = init_test_plugin()
        return
    return _import_module(name)


def test_plugins(monkeypatch, capsys):
    monkeypatch.setattr(spy.cli, 'iter_modules', iter_modules)
    monkeypatch.setattr(spy.cli, 'import_module', import_module)

    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    sys.argv = sys.argv[0:1] + ['-h']
    spy._dont_load_plugins = False
    with pytest.raises(SystemExit):
        from spy import __main__
    spy._dont_load_plugins = True
    out, err = capsys.readouterr()
    assert err == ''

    monkeypatch.setattr(sys, 'stdin', io.StringIO(""))
    sys.argv = sys.argv[0:1] + ['xyz']
    with pytest.raises(SystemExit):
        from spy import __main__
    out, err = capsys.readouterr()
    assert out == 'abc123\n'
    assert err == ''

    monkeypatch.setattr(sys, 'stdin', io.StringIO("foo bar quux"))
    sys.argv = sys.argv[0:1] + ['--_test_plugin_uppercase', 'pipe']
    with pytest.raises(SystemExit):
        from spy import __main__
    out, err = capsys.readouterr()
    assert out == 'FOO BAR QUUX\n'
    assert err == ''
