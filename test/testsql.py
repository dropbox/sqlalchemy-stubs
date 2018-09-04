"""Mypy style test cases for SQLAlchemy stubs and plugin."""

import os
import os.path

import pytest  # type: ignore  # no pytest in typeshed

from mypy.defaults import PYTHON3_VERSION
from mypy.test.config import test_temp_dir
from mypy.test.data import DataDrivenTestCase, DataSuite
from mypy.test.helpers import assert_string_arrays_equal
from mypy import api


class SQLDataSuite(DataSuite):
    files = ['sqlalchemy-basics.test']
    data_prefix = '/home/ivan/Devel/sqlalchemy-stubs/test/test-data'

    def run_case(self, testcase: DataDrivenTestCase) -> None:

        assert testcase.old_cwd is not None, "test was not properly set up"
        mypy_cmdline = [
            '--show-traceback',
            '--no-silence-site-packages',
        ]
        py2 = testcase.name.lower().endswith('python2')
        if py2:
            mypy_cmdline.append('--py2')
        else:
            mypy_cmdline.append('--python-version={}'.format('.'.join(map(str, (3, 4)))))

        # Write the program to a file.
        program_path = os.path.join(test_temp_dir, 'main.py')
        mypy_cmdline.append(program_path)
        with open(program_path, 'w') as file:
            for s in testcase.input:
                file.write('{}\n'.format(s))
        output = []
        # Type check the program.
        out, err, returncode = api.run(mypy_cmdline)
        # split lines, remove newlines, and remove directory of test case
        for line in (out + err).splitlines():
            if line.startswith(test_temp_dir + os.sep):
                output.append(line[len(test_temp_dir + os.sep):].rstrip("\r\n"))
            else:
                output.append(line.rstrip("\r\n"))
        # Remove temp file.
        os.remove(program_path)
        assert_string_arrays_equal(testcase.output, output,
                                   'Invalid output ({}, line {})'.format(
                                   testcase.file, testcase.line))
