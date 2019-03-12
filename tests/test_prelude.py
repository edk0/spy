from spy import prelude

def test_id():
    x = object()
    assert prelude.id(x) is x


def test_ft():
    def f(x):
        return x + 1
    assert prelude.ft(f, f, f)(1) == (2, 2, 2)
