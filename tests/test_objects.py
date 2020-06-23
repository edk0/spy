import pytest

import builtins
import io
from io import StringIO, UnsupportedOperation

import spy, spy.core
from spy.objects import Context, SpyFile, _ModuleProxy, _FunctionWrapper

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

    with pytest.raises(AttributeError):
        mp._test_

    assert dir(mp) == dir(spy)
    assert repr(mp) == repr(spy)


@pytest.fixture
def context():
    c = Context(_pipe_name='pipe')
    c.update(builtins.__dict__)
    return c


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

    def test_view_get(self, context):
        v = context.view()
        assert v.get('foo', 'bar') == 'bar'
        v['foo'] = 'qux'
        assert v.get('foo', 'bar') == 'qux'

    def test_repr(self, context):
        c = context
        repr(c)
        v = c.view()
        repr(v)

    def test_auto_import(self, context):
        spy._test_ = []
        assert context['spy']._test_ is spy._test_


class TestFunctionWrapping:
    def test_builtins_are_wrapped(self, context):
        c = context.view()
        (c['max'] + 1)([1, 2, 3])

    def test_wrapped_left_op(self):
        f = _FunctionWrapper(len)
        two = lambda _: 2
        ftwo = _FunctionWrapper(two)
        assert (f//2)([1,1,1,1]) == 2
        assert (f//two)([1,1,1,1]) == 2
        assert (f//ftwo)([1,1,1,1]) == 2

    def test_wrapped_right_op(self):
        f = _FunctionWrapper(len)
        eight = lambda _: 8
        assert (8//f)([1,1,1,1]) == 2
        assert (eight//f)([1,1,1,1]) == 2

    def test_wrapped_unary_op(self):
        def id(x): return x
        f = _FunctionWrapper(id)
        assert (-f)(7) == -7

    def test_wrapper_repr(self):
        def f(x): pass
        assert repr(f) == repr(_FunctionWrapper(f))
        f = _FunctionWrapper(f)
        assert repr(f+2) == 'add(f,2)'
        assert repr(f*3+2) == 'add(mul(f,3),2)'

    def test_wrapper_eq(self):
        def f(x): return x + 2
        f = _FunctionWrapper(f)
        assert (f == 11)(9) is True

    def test_only_missing(self):
        f = _FunctionWrapper(lambda x: x * 2)
        assert f(5) == 10
        assert (f + 2)(5) == 12
        class CallableWithAddition:
            def __init__(self, a):
                self.a = a
            def __call__(self, x):
                return self.a * x
            def __add__(self, other):
                return self.__class__(self.a + other)
        c = CallableWithAddition(2)
        f = _FunctionWrapper(c)
        assert f(5) == 10
        assert (f + 2)(5) == 20


@pytest.fixture
def spyfile():
    return SpyFile(StringIO(TEST_INPUT))


class TestSpyFile:
    def test_read(self, spyfile):
        assert spyfile.read(27) == TEST_INPUT[:27]
        assert spyfile.read(0) == ''
        assert spyfile.read() == TEST_INPUT[27:]

    def test_len(self, spyfile):
        assert len(spyfile) == len(TEST_INPUT.splitlines())

    def test_readline(self, spyfile):
        spyfile.read(5)
        assert spyfile.readline() == 'is a test input\n'
        assert spyfile.readline(8) == 'for use '
        assert spyfile.read() == TEST_INPUT[29:]
        assert spyfile.readline() == ''

    def test_readline_finishes(self, spyfile):
        for _ in range(TEST_INPUT.count('\n') + 2):
            a = spyfile.readline()
        assert a == ''

    def test_iter(self, spyfile):
        for spy, line in zip(iter(spyfile), TEST_INPUT.splitlines()):
            assert spy == line

    def test_index(self, spyfile):
        assert spyfile[2] == 'here'
        assert list(spyfile[3::2]) == ['are', 'more', 'of']

    def test_str(self, spyfile):
        assert str(spyfile) == TEST_INPUT

    def test_detach(self, spyfile):
        with pytest.raises(UnsupportedOperation):
            spyfile.detach()

    def test_positioning(self):
        f = SpyFile(StringIO("foobar\n123456789\nhello\nasdfasdfasdfasdfcheese"))
        assert f.read(3) == 'foo'
        assert f.readline() == 'bar\n'
        assert f.seek(10, io.SEEK_CUR) == 17
        assert f.readline() == 'hello\n'
        assert f.seek(-7, io.SEEK_END) == 39
        assert f.read() == 'cheese'
        assert f.seek(0) == 0
        assert f.readline() == 'foobar\n'

        f = SpyFile(StringIO("foobar\n123456789\nhello\nasdfasdfasdfasdfcheese"))
        assert f.seek(17) == 17
        assert f.readline() == 'hello\n'

        f = SpyFile(StringIO("foobar\n123456789\nhello\nasdfasdfasdfasdfcheese"))
        assert f.seek(-7, io.SEEK_END) == 39
        assert f.read() == 'cheese'

        with pytest.raises(ValueError):
            f.seek(0, -10)

        assert f.seek(-1000) == 0
        assert f.seek(1000) == 46
