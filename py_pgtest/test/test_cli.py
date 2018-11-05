from ..cli import *


def test_cli():
    main = Main()
    args = main.parse([])
    assert args.watch is False
    assert args.init_script == '__init__.sql'

    args = main.parse(['--watch'])
    assert args.watch is True
