# py-pgtest

A primitive script to make running postgresql unit-tests less painful.

Requires postgresql server, pgtap and python (>=3.6) installed.

After installation with 
```bash
pip install py-pgtest
```
you can go into a directory and run
```bash
pgtest --pg-uri postgres://user:password@host:port/database
```
and the system will:
* first run `__nuke__.sql` in the current directory using psql, 
* then run `__init__.sql` in the current directory to do the db initialization (hint: you can
use `\ir` in your script to achieve some structure),
* finally run all `test_*.sql` files found in the subdirectories.

The tests should be written in [pgtap](https://pgtap.org/) style, and the test results
will be displayed using python's unittest style.

If the argument `--watch` is given, pgtest will watch changes to any
`.sql` files, and rerun the tests when changes occur.

There are other options that you can use, e.g. choosing directories other than
the current one. For details, run `pgtest -h`