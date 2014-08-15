import sys

import spy
from spy import catcher, decorators


@spy.fragment
def _exception_undecorated(v):
    raise Exception


def test_undecorated(capsys):
    seq = [_exception_undecorated]
    with catcher.hook():
        try:
            spy.chain(seq).run_to_exhaustion()
        except Exception:
            sys.excepthook(*sys.exc_info())
    out, err = capsys.readouterr()
    assert any(s.startswith('  Fragment 1') for s in err.splitlines())


@spy.fragment
@decorators.callable
def _exception_in_decorator(v):
    return None  # probably not callable


def test_in_decorator(capsys):
    seq = [_exception_in_decorator]
    with catcher.hook():
        try:
            spy.chain(seq).run_to_exhaustion()
        except Exception:
            sys.excepthook(*sys.exc_info())
    out, err = capsys.readouterr()
    assert any(s.startswith('  Fragment 1, in decorator spy.decorators.callable') for s in err.splitlines())

