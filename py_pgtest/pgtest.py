import os
import re
import subprocess
import sys
import tempfile
import tap.loader
import tap.parser
import shutil
import unittest
import colorama

TIMEOUT = 20
DEFAULT_TEST_SCRIPT_PATTERN = re.compile(r'.+\.test\.sql$')
DEFAULT_PGTAP_INIT_FILE = os.path.join(os.path.dirname(__file__), 'pgtap_prefix.sql')

colorama.init()


def _construct_psql_command(psql, uri):
    return [psql, '-d', uri, '-v', 'ON_ERROR_STOP=1']


def discover_test_scripts(basepath, pattern=DEFAULT_TEST_SCRIPT_PATTERN):
    tests = []
    for dirpath, _, filenames in os.walk(basepath):
        for filename in filenames:
            if pattern.match(filename):
                tests.append(os.path.join(dirpath, filename))
    return tests


def run_script(uri, paths, psql, encoding='utf-8', check=True):
    command = _construct_psql_command(psql, uri)
    for path in paths:
        command.append('-f')
        command.append(path)
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
    stdout, stderr = run_script(uri=uri, paths=[fname], psql=psql, encoding=encoding, check=check)
    os.remove(fname)
    return stdout, stderr


def _read_file_content(base_path, path):
    if path is None:
        _path = base_path
    else:
        _path = os.path.join(base_path, path)
    with open(_path, 'r', encoding='utf-8') as f:
        return f.read()


def run_tests(uri, psql, base_path, init_script, nuke_script, test_script, verbose=False, stream=sys.stderr,
              pgtap_init_file=DEFAULT_PGTAP_INIT_FILE, init_only=False, nuke_only=False, no_init_nuke=False):
    skip_tests = init_only or nuke_only

    if (not skip_tests and not no_init_nuke) or nuke_only:
        print('-> Running cleanup script')
        run_script(uri, [os.path.join(base_path, nuke_script)], psql)

    if (not skip_tests) or init_only:
        print('-> Running initialization script')
        run_script(uri, [os.path.join(base_path, init_script)], psql)

    if skip_tests:
        return

    print('-> Running test initialization script')
    run_script(uri, [os.path.join(base_path, test_script)], psql)

    scripts_to_test = discover_test_scripts(base_path)
    tmpdir = os.path.join(tempfile.gettempdir(), 'pgtest')
    os.makedirs(tmpdir, exist_ok=True)
    tap_files = []
    print('-> Running tests')

    runner = unittest.TextTestRunner(verbosity=verbose, stream=stream)
    parser = tap.parser.Parser()
    for path in scripts_to_test:
        stdout, stderr = run_script(uri, [pgtap_init_file, path], psql, check=False)
        is_error = False
        for l in parser.parse_text(stdout):
            if l.category == 'test' and not l.ok:
                is_error = True
                print(f'{colorama.Fore.RED}{l}{colorama.Style.RESET_ALL}')
            elif is_error and l.category == 'diagnostic':
                print(f'{colorama.Fore.RED}{l.text}{colorama.Style.RESET_ALL}')
            else:
                is_error = False

        if stderr:
            print('========================= captured stderr ============================')
            print(f'{colorama.Fore.RED}{stderr}{colorama.Style.RESET_ALL}', file=sys.stderr)
        relpath = os.path.relpath(path, base_path)
        outpath = os.path.join(tmpdir, relpath)
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
