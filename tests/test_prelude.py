from spy import prelude

def test_id():
    x = object()
    assert prelude.id(x) is x


def test_ft():
    def f(x):
        return x + 1
    assert prelude.ft(f, f, f)(1) == (2, 2, 2)


def test_mt():
    def f(x):
        return x * 7
    assert prelude.mt(f, f, f)((1, 2, 3)) == (7, 14, 21)


def test_sum():
    l = [1,2,3]
    assert prelude.sum(l) == 6

    l = [1.,2.,3.]
    assert prelude.sum(l) == sum(l)

    l = ['abc', 'def', 'ghi']
    assert prelude.sum(l, '') == 'abcdefghi'

    l = [[1], [2, 3], [4, 5, 6]]
    assert prelude.sum(l, []) == [1, 2, 3, 4, 5, 6]
    assert l == [[1], [2, 3], [4, 5, 6]]
