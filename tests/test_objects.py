import pytest

from io import StringIO

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
def spyfile():
    return SpyFile(StringIO(TEST_INPUT))


class TestSpyFile:
    def test_read(self, spyfile):
        assert spyfile.read(27) == TEST_INPUT[:27]
        assert spyfile.read() == TEST_INPUT[27:]

    def test_iter(self, spyfile):
        for spy, line in zip(spyfile, TEST_INPUT.splitlines()):
            assert spy == line

    def test_str(self, spyfile):
        assert str(spyfile) == TEST_INPUT
        assert spyfile.replace('a', '!') == TEST_INPUT.replace('a', '!')
