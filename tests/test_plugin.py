import io
import sys

import pytest

import spy
import spy.cli
from spy import prelude
from spy.decorators import decorator


class FakeEntryPoint:
    def __init__(self, name, value):
        self.name = name
        self._value = value

    def load(self):
        return self._value


def init_test_plugin():
    prelude.xyz = 'abc123'
    prelude.__all__ += ['xyz']

    @decorator('--_test_plugin_uppercase', doc='Make the result uppercase')
    def uppercase(fn, v, context):
        return str(fn(v, context)).upper()


def iter_entry_points(_):
    yield FakeEntryPoint('test_plugin', init_test_plugin)


def test_plugins(monkeypatch, capsys):
    monkeypatch.setattr(spy.cli, 'iter_entry_points', iter_entry_points)

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
