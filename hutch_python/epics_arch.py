"""Module to help create the epicsArch file that will be read by the DAQ"""
import argparse
import happi
import logging
import sys
from happi.backends.qs_db import QSBackend
import os
from .constants import EPICS_ARCH_FILE_PATH

logger = logging.getLogger(__name__)

# Simple Argument Parser Setup
parser = argparse.ArgumentParser(description='Create an epicsArch file from'
                                             ' the Quesionnaire')

parser.add_argument('experiment', nargs="?", help='Experiment name to'
                    ' create the epicsArch file from. E.g.: xpplv6818')

parser.add_argument('--hutch', action="store",
                    help='Hutch name to create the epicsArch for. E.g.: xpp')

parser.add_argument('--path', action="store",
                    help='Path to create the epicsArch file to.')

parser.add_argument('--dry-run', action='store_true', default=False,
                    help='Print to stdout what would be written in the '
                         'archFIle.')


def epics_arch_qs(args):
    args = parser.parse_args(args)

    if args.experiment and not args.dry_run:
        logger.info('Creating epicsArch file for experiment: %s',
                    args.experiment)
        print('HELLO --- for now')
        # create_file(exp_name)
    elif args.hutch:
        # Overwrite the default hutch
        print(f'HUTCH----------------- {args.hutch}')
        # EPICS_ARCH_FILE_PATH.format(hutch)
    elif args.path:
        # Overwrite the default path
        print(f'PATH----------------- {args.path}')
    elif args.dry_run:
        if args.experiment:
            print_dry_run(args.experiment)
        else:
            logger.error('Please provide an experiment name.')
            return
    else:
        parser.print_usage()
        return


def print_dry_run(exp_name):
    """
    Print to stdou the data that would be stored in the epicsArch file.

    Parameters
    ----------
    exp_name : str
        Experiment name, e.g.: xpplv6818

    Examples
    --------
    >>> epicsarch-qs xpplv6818 --dry-run
    """
    data = get_questionnaire_data(exp_name)
    for item in data:
        print(item)


def get_questionnaire_data(exp_name):
    """
    Returns a list of items that would be written in the epicsArch file.

    Parameters
    ----------
    exp_name : str
        Experiment name, e.g.: xpplv6818

    Returns
    -------
    data_list : list
        List containing the names ans prefixes of items in the Questionnaire.
    """
    data_list = []
    qs_client = happi.Client(database=QSBackend(exp_name, use_kerberos=True))
    # qs_client = happi.Client(
    #    path='/home/cristina/workspace/device_config/db.json')
    items = qs_client.all_items
    if not items:
        logger.warning("No devices found in PCDS Questionnaire for %s",
                       exp_name)
        return
    else:
        for item in items:
            name = ''.join(('* ', item.name))
            data_list.append(name)
            data_list.append(item.prefix)
    return data_list


def create_file(exp_name, path=None):
    """
    Create a file with aliases and pvs from the questionnaire.
    """
    data_list = get_questionnaire_data(exp_name)
    hutch = exp_name[0:3]
    path = path or EPICS_ARCH_FILE_PATH.format(hutch)
    # path = path or '/home/cristina/workspace/hutch-python/'
    if not os.path.exists(path):
        raise IOError('Invalid path: %s' % path)
    exp_name = str(exp_name)
    file_path = ''.join((path, 'epicsArch_', exp_name, '.txt'))
    with open(file_path, 'w') as f:
        for data in data_list:
            try:
                f.write(f'{data}\n')
            except OSError as ex:
                logger.error('Could not write file %s, %s', file_path, ex)


def main():
    """Execute the ``epics_arch`` with command line arguments."""
    epics_arch_qs(sys.argv[1:])
