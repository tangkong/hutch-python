#!/usr/bin/env python
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

if __name__ == '__main__':
    # Show output results from every test function
    # Show the message output for skipped and expected failures
    args = ['-v', '-vrxs']

    # Add extra arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    txt = 'pytest arguments: {}'.format(args)
    print(txt)

    # Setup logger and log everything to a file
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    log_dir = Path(os.path.dirname(__file__)) / 'logs'
    log_file = log_dir / 'run_tests_log.txt'

    if not log_dir.exists():
        log_dir.mkdir(parents=True)
    if log_file.exists():
        do_rollover = True
    else:
        do_rollover = False

    handler = RotatingFileHandler(str(log_file), backupCount=5,
                                  encoding=None, delay=0)
    if do_rollover:
        handler.doRollover()
    formatter = logging.Formatter(fmt=('%(asctime)s.%(msecs)03d '
                                       '%(module)-15s '
                                       '%(levelname)-8s '
                                       '%(threadName)-10s '
                                       '%(message)s'),
                                  datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    logger = logging.getLogger(__name__)
    logger.info(txt)

    sys.exit(pytest.main(args))
