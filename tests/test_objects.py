import pytest

from io import StringIO, UnsupportedOperation

import spy, spy.core
from spy.objects import Context, SpyFile, _ModuleProxy

TEST_INPUT = '''this is a test input
for use by a SpyFile
here
are
some
more
lines
of
it'''


def test_module_proxy():
    mp = _ModuleProxy(spy)
    spy._test_ = []
    spy.core._test_ = []
    assert mp._test_ is spy._test_

    spy_core = spy.core
    del spy.core
    assert mp.core._test_ is spy_core._test_
    spy.core = spy_core

    mp._test_ = []
    assert spy._test_ is mp._test_

    del mp._test_
    with pytest.raises(AttributeError):
        spy._test_

    assert dir(mp) == dir(spy)
    assert repr(mp) == repr(spy)


@pytest.fixture
def context():
    return Context(_pipe_name='pipe')


class TestContext:
    def test_view(self, context):
        PIPE_NAME = 'pipe'

        c = context
        c['test'] = 'fubar'
        c[PIPE_NAME] = 'foo'
        v = c.view()
        v.overlay[PIPE_NAME] = 'bar'

        assert v['test'] == 'fubar'
        v['test'] = '123'
        assert c['test'] == '123'

        assert 'test' in v and 'test' in c
        del v['test']
        assert 'test' not in v and 'test' not in c

        assert v[PIPE_NAME] == 'bar'
        v[PIPE_NAME] = 'baz'
        assert v[PIPE_NAME] == 'baz'
        with pytest.raises(TypeError):
            del v[PIPE_NAME]

        assert c[PIPE_NAME] == 'foo'

    def test_repr(self, context):
        c = context
        repr(c)
        v = c.view()
        repr(v)

    def test_auto_import(self, context):
        spy._test_ = []
        assert context['spy']._test_ is spy._test_


@pytest.fixture
def spyfile():
    return SpyFile(StringIO(TEST_INPUT))


class TestSpyFile:
    def test_read(self, spyfile):
        assert spyfile.read(27) == TEST_INPUT[:27]
        assert spyfile.read(0) == ''
        assert spyfile.read() == TEST_INPUT[27:]

    def test_len(self, spyfile):
        with pytest.raises(TypeError):
            len(spyfile)

    def test_readline(self, spyfile):
        spyfile.read(5)
        assert spyfile.readline() == 'is a test input\n'
        assert spyfile.readline(8) == 'for use '
        assert spyfile.read() == TEST_INPUT[29:]
        assert spyfile.readline() == ''

    def test_iter(self, spyfile):
        for spy, line in zip(iter(spyfile), TEST_INPUT.splitlines()):
            assert spy == line

    def test_index(self, spyfile):
        assert spyfile[2] == 'here'
        assert list(spyfile[3::2]) == ['are', 'more', 'of']

    def test_str(self, spyfile):
        assert str(spyfile) == TEST_INPUT
        assert spyfile.replace('a', '!') == TEST_INPUT.replace('a', '!')

    def test_detach(self, spyfile):
        with pytest.raises(UnsupportedOperation):
            spyfile.detach()
