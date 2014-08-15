import spy.main
from spy.objects import Context


class TestCompile:
    def test_expr(self):
        code, is_expr = spy.main.compile_('3 + 4')
        assert is_expr
        assert eval(code) == 7

    def test_exec(self):
        code, is_expr = spy.main.compile_('x = True')
        assert not is_expr

        scope = {}
        eval(code, scope, scope)
        assert scope.get('x') is True


def test_make_callable():
    context = Context(_pipe_name='pipe')
    code, is_expr = spy.main.compile_('x = pipe.upper(); pipe = x[::-1]')
    ca = spy.main.make_callable(code, is_expr, context)
    assert ca('bar') == 'RAB'


def test_get_imports():
    co, is_expr = spy.main.compile_('abc.defg(foo.bar)')
    assert set(spy.main.get_imports(co)) >= {'abc', 'foo', 'foo.bar'}


def test_make_context():
    context = spy.main.make_context(['collections', 'i am pretty sure this module does not exist'])
    assert 'collections' in context
