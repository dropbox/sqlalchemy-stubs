"""Mypy style test cases for SQLAlchemy stubs and plugin."""

import os
import os.path
import sys
import re

import pytest  # type: ignore  # no pytest in typeshed

from mypy.test.config import test_temp_dir
from mypy.test.data import DataDrivenTestCase, DataSuite
from mypy.test.helpers import assert_string_arrays_equal
from mypy.util import try_find_python2_interpreter
from mypy import api

this_file_dir = os.path.dirname(os.path.realpath(__file__))
prefix = os.path.dirname(this_file_dir)
inipath = os.path.abspath(os.path.join(prefix, 'test'))

# Locations of test data files such as test case descriptions (.test).
test_data_prefix = os.path.join(prefix, 'test', 'test-data')


class SQLDataSuite(DataSuite):
    if sys.version_info[:2] == (3, 5):
        files = ['sqlalchemy-basics.test']
    else:
        files = ['sqlalchemy-basics.test',
                 'sqlalchemy-functions.test',
                 'sqlalchemy-sql-elements.test',
                 'sqlalchemy-sql-sqltypes.test',
                 'sqlalchemy-sql-selectable.test',
                 'sqlalchemy-sql-schema.test',
                 'sqlalchemy-plugin-features.test']
    data_prefix = test_data_prefix

    def run_case(self, testcase: DataDrivenTestCase) -> None:

        assert testcase.old_cwd is not None, "test was not properly set up"
        mypy_cmdline = [
            '--show-traceback',
            '--no-silence-site-packages',
            '--no-error-summary',
            '--config-file={}/sqlalchemy.ini'.format(inipath),
        ]
        py2 = testcase.name.lower().endswith('python2')
        if py2:
            if try_find_python2_interpreter() is None:
                pytest.skip()
                return
            mypy_cmdline.append('--py2')
        else:
            if sys.version_info[:2] == (3, 5):
                version = (3, 6)  # Always accept variable annotations.
            else:
                version = sys.version_info[:2]
            mypy_cmdline.append('--python-version={}'.format('.'.join(map(str, version))))

        program_text = '\n'.join(testcase.input)
        flags = re.search('# flags: (.*)$', program_text, flags=re.MULTILINE)
        if flags:
            flag_list = flags.group(1).split()
            mypy_cmdline.extend(flag_list)

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
                output.append(line[len(test_temp_dir + os.sep):].rstrip("\r\n").replace('.py',
                                                                                        ''))
            else:
                output.append(line.rstrip("\r\n"))
        # Remove temp file.
        os.remove(program_path)
        assert_string_arrays_equal(testcase.output, output,
                                   'Invalid output ({}, line {})'.format(
                                   testcase.file, testcase.line))
