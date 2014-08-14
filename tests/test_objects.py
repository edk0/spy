import pytest

from io import StringIO, UnsupportedOperation

import spy
from spy.objects import Context, SpyFile

TEST_INPUT = '''this is a test input
for use by a SpyFile
here
are
some
more
lines
of
it'''


@pytest.fixture
def context():
    return Context(_pipe_name='pipe')


class TestContext:
    def test_update(self, context):
        c = context
        c += {'foo': 'bar'}
        assert any(item == ('foo', 'bar') for item in c.items())

        with pytest.raises(TypeError):
            c += 3

    def test_view(self, context):
        c = context
        c['test'] = 'fubar'
        c[c.pipe_name] = 'foo'
        v = c.pipe_view('bar')

        assert v['test'] == 'fubar'
        v['test'] = '123'
        assert c['test'] == '123'

        assert 'test' in v and 'test' in c
        del v['test']
        assert 'test' not in v and 'test' not in c

        assert v[c.pipe_name] == 'bar'
        v[c.pipe_name] = 'baz'
        assert v[c.pipe_name] == 'baz'
        with pytest.raises(TypeError):
            del v[c.pipe_name]

        assert c[c.pipe_name] == 'foo'

    def test_repr(self, context):
        c = context
        repr(c)
        v = c.pipe_view('test')
        repr(v)


@pytest.fixture
def spyfile():
    return SpyFile(StringIO(TEST_INPUT))


class TestSpyFile:
    def test_read(self, spyfile):
        assert spyfile.read(27) == TEST_INPUT[:27]
        assert spyfile.read(0) == ''
        assert spyfile.read() == TEST_INPUT[27:]

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
        assert spyfile[3::2] == ['are', 'more', 'of']

    def test_str(self, spyfile):
        assert str(spyfile) == TEST_INPUT
        assert spyfile.replace('a', '!') == TEST_INPUT.replace('a', '!')
        assert repr(spyfile) == repr(TEST_INPUT)

    def test_detach(self, spyfile):
        with pytest.raises(UnsupportedOperation):
            spyfile.detach()
