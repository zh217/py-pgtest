import os
import re
import subprocess
import sys
import tempfile
import tap.loader
import shutil
import unittest

TIMEOUT = 20


def _construct_psql_command(psql, uri):
    return [psql, '-d', uri]


DEFAULT_TEST_SCRIPT_PATTERN = re.compile(r'^test_.+\.sql$')


def discover_test_scripts(basepath, pattern=DEFAULT_TEST_SCRIPT_PATTERN):
    tests = []
    for dirpath, _, filenames in os.walk(basepath):
        for filename in filenames:
            if pattern.match(filename):
                tests.append(os.path.join(dirpath, filename))
    return tests


def run_script(uri, path, script, psql, encoding='utf-8', check=True):
    if script is not None:
        script_full_path = os.path.join(path, script)
    else:
        script_full_path = path
    command = _construct_psql_command(psql, uri) + ['-f', script_full_path]
    proc = subprocess.run(command,
                          check=check,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          timeout=TIMEOUT)
    return proc.stdout.decode(encoding), proc.stderr.decode(encoding)


def run_string(uri, psql, content, encoding='utf-8', check=True):
    with tempfile.NamedTemporaryFile(mode='w', encoding=encoding, delete=False, suffix='.sql') as f:
        fname = f.name
        f.write(content)
    stdout, stderr = run_script(uri=uri, path=fname, script=None, psql=psql, encoding=encoding, check=check)
    os.remove(fname)
    return stdout, stderr


def _read_file_content(base_path, path):
    if path is None:
        _path = base_path
    else:
        _path = os.path.join(base_path, path)
    with open(_path, 'r', encoding='utf-8') as f:
        return f.read()


def _get_non_base_path(base_path, path):
    base_path = os.path.abspath(base_path)
    path = os.path.abspath(path)
    return path[len(base_path):]


def run_tests(uri, psql, base_path, test_script, init_script, nuke_script, verbose=False, stream=sys.stderr):
    print('-> Running cleanup script')
    run_script(uri, base_path, nuke_script, psql)
    print('-> Running initialization script')
    run_script(uri, base_path, init_script, psql)
    test_init_content = _read_file_content(base_path, test_script)
    scripts_to_test = [(_get_non_base_path(base_path, f), test_init_content + '\n' + _read_file_content(f, None)) for f
                       in discover_test_scripts(base_path)]
    tmpdir = os.path.join(tempfile.gettempdir(), 'pgtest')
    os.makedirs(tmpdir, exist_ok=True)
    tap_files = []
    print('-> Running tests')

    runner = unittest.TextTestRunner(verbosity=verbose, stream=stream)

    for rel_path, script in scripts_to_test:
        stdout, stderr = run_string(uri, psql, script, check=False)
        if stdout:
            for l in stdout.splitlines():
                if l.startswith('# '):
                    print(l, file=sys.stderr)
        if stderr:
            # print('captured stderr')
            print(stderr, file=sys.stderr)
        outpath = os.path.join(tmpdir, rel_path)
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(stdout)
        tap_files.append(outpath)
    loader = tap.loader.Loader()
    suite = loader.load(tap_files)
    shutil.rmtree(tmpdir)
    result = runner.run(suite)
    return _get_status(result)


def _get_status(result):
    """Get a return status from the result."""
    if result.wasSuccessful():
        return 0
    else:
        return 1
