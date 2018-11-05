import os
import pytest

from ..pgtest import *


@pytest.fixture
def pg_script_path():
    cur_dir = os.path.dirname(__file__)
    path = os.path.join(cur_dir, '..', '..', '..', 'pg')
    return os.path.abspath(path)


@pytest.fixture
def pg_uri():
    return 'postgres://postgres:ubdugus@127.0.0.1/postgres'


def test_run_script(pg_script_path, pg_uri):
    run_script(uri=pg_uri, path=pg_script_path, script='__nuke__.sql', psql='psql')
    run_script(uri=pg_uri, path=pg_script_path, script='__init__.sql', psql='psql')
    run_script(uri=pg_uri, path=pg_script_path, script='__test__.sql', psql='psql')


def test_run_string(pg_script_path, pg_uri):
    txt_path = os.path.join(pg_script_path, '__nuke__.sql')
    with open(txt_path, 'r', encoding='utf-8') as f:
        txt_content = f.read()

    run_string(uri=pg_uri, psql='psql', content=txt_content)


def test_discovery(pg_script_path):
    tests = discover_test_scripts(pg_script_path)
    assert tests


def test_run(pg_script_path, pg_uri):
    run_tests(uri=pg_uri,
              psql='psql',
              base_path=pg_script_path,
              test_script='__test__.sql',
              init_script='__init__.sql',
              nuke_script='__nuke__.sql')
