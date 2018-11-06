import argparse
import time
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler
from py_pgtest.pgtest import *
import traceback
import subprocess
import colorama


class RunOnChange(RegexMatchingEventHandler):
    def __init__(self):
        super().__init__(regexes=[r'.+\.sql$'], case_sensitive=False, ignore_directories=False)
        self.should_run_for_file = None

    def on_modified(self, event):
        self.should_run_for_file = event.src_path


class Main:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Continuously testing postgres')

        parser.add_argument('--dir', default='.', help='default folder to find SQL script')
        parser.add_argument('--pg-uri', help='how to connect to postgres testing server', required=True)
        parser.add_argument('--watch', action='store_true', help='continuously monitor for changes')
        parser.add_argument('--init-script', default='__init__.sql', help='name of database initialization script')
        parser.add_argument('--nuke-script', default='__nuke__.sql',
                            help='name of nuking script for wiping database clean')
        parser.add_argument('--psql', default='psql', help='path to psql executable to use')

        self.parser = parser

    def parse(self, argv):
        return self.parser.parse_args(argv)

    def __call__(self, argv):
        parsed = self.parse(argv)
        if parsed.watch:
            self.run_forever(parsed)
        else:
            self.run_once(parsed)

    def run_forever(self, parsed):
        self.run_once(parsed)
        event_handler = RunOnChange()
        observer = Observer()
        observer.schedule(event_handler, parsed.dir, recursive=True)
        observer.start()
        try:
            while True:
                if event_handler.should_run_for_file:
                    time.sleep(1)
                    print()
                    print('-> Detected file change:', event_handler.should_run_for_file)
                    event_handler.should_run_for_file = None
                    self.run_once(parsed)
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def run_once(self, parsed):
        try:
            run_tests(uri=parsed.pg_uri,
                      psql=parsed.psql,
                      base_path=parsed.dir,
                      init_script=parsed.init_script,
                      nuke_script=parsed.nuke_script)
        except subprocess.CalledProcessError as e:
            traceback.print_exc()
            if e.stdout:
                print('========================= captured stdout ============================')
                print(e.stdout.decode('utf-8'), file=sys.stderr)
            if e.stderr:
                print('========================= captured stderr ============================')
                print(f'{colorama.Fore.RED}{e.stderr.decode("utf-8")}{colorama.Style.RESET_ALL}', file=sys.stderr)


def main():
    args = sys.argv or []
    Main()(args[1:])


if __name__ == '__main__':
    main()
