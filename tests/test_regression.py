import locale
import os.path
import subprocess

import pytest


where = os.path.dirname(__file__)


def collect_tests():
    with open(os.path.join(where, 'regression_tests')) as f:
        tests = [x.strip() for x in f]
    while tests:
        test_line = tests.pop(0)
        if not test_line or test_line.startswith('#'):
            continue
        expected_output = []
        while tests and tests[0].startswith('> '):
            expected_output.append(tests.pop(0)[2:])
        if expected_output:
            expected_output = '\n'.join(expected_output + [''])
        else:
            expected_output = None
        yield test_line, expected_output


@pytest.mark.parametrize(('test_line', 'expected_output'), list(collect_tests()))
def test_regression(test_line, expected_output):
    encoding = locale.getpreferredencoding(False)
    output = subprocess.check_output(test_line,
                                     cwd=where,
                                     shell=True)
    output = output.decode(encoding)
    if expected_output:
        assert output == expected_output
