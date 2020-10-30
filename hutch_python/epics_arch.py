"""Module to help create the epicsArch file that will be read by the DAQ."""
import argparse
import logging
import os
import sys

import happi
from happi.backends.qs_db import QSBackend

import hutch_python.constants

from .constants import EPICS_ARCH_FILE_PATH

logger = logging.getLogger(__name__)

# Simple Argument Parser Setup
parser = argparse.ArgumentParser(description='Create an epicsArch file from'
                                             ' the Quesionnaire')

parser.add_argument('experiment', nargs='?', help='Experiment name to'
                    ' create the epicsArch file from. E.g.: xpplv6818')

parser.add_argument('--hutch', action="store",
                    help='Hutch name to create the epicsArch file for.'
                    ' E.g.: xpp')

parser.add_argument('--path', action="store",
                    help='Path to create the epicsArch file.'
                    ' E.g.: /path/to/the/directory/')

parser.add_argument('--dry-run', action='store_true', default=False,
                    help='Print to stdout what would be written in the '
                         'archFIle.')


def epics_arch_qs(args):
    """
    Command Line for epicsarch-qs.

    Parameter
    ---------
    args : list
        Arguments passed to epicsarch-qs.

    Examples
    --------
    Create the epicsArch file for experiment `xpplv6818`. If no `--path` or
    `--hutch` provided, write the file at the default path:
    `/cds/group/pcds/dist/pds/{}/misc/` whre {} is the hutch name from the
    experiment (`xpp`):

    >>> epicsarch-qs xpplv6818

    Would write: `/cds/group/pcds/dist/pds/xpp/misc/epicsArch_xpplv6818.txt`

    To change the path where you want to write the epicsArch file:

    >>> epicsarch-qs xpplv6818 --path /my/new/path/

    Would write: `/my/new/path/epicsArch_xpplv6818.txt`

    To change only the hutch name in the path:

    >>> epicsarch-qs xpplv6818 --hutch xcs

    Would write: `/cds/group/pcds/dist/pds/xcs/misc/epicsArch_xpplv6818.txt`

    To print to standard output what would be written in the epicsArch file:

    >>> epicsarch-qs xpplv6818 --dry-run
    """
    args = parser.parse_args(args)

    if args.experiment and not args.dry_run:
        # set the path to write the epicsArch file to.
        if args.path:
            overwrite_path(args.path)
        elif args.hutch:
            overwrite_hutch(args.hutch)
        else:
            set_path(args.experiment)
        create_file(args.experiment)
    elif args.hutch:
        overwrite_hutch(args.hutch)
    elif args.path:
        overwrite_path(args.path)
    elif args.dry_run:
        if args.experiment:
            print_dry_run(args.experiment)
        else:
            logger.error('Please provide an experiment name.')
            return
    else:
        parser.print_usage()
        return


def overwrite_hutch(hutch_name):
    """
    Overwrite the default Hutch.

    Parameters
    ----------
    hutch_name : str
        Name of the hutch, e.g.: xpp
    """
    if hutch_name:
        hutch_python.constants.EPICS_ARCH_FILE_PATH = (
            EPICS_ARCH_FILE_PATH.format(hutch_name.lower())
        )


def overwrite_path(path):
    """
    Overwrite the default path.

    Parameters
    ----------
    path : str
        Path where to write the epicsArch file to.
    """
    if path and not os.path.exists(path):
        raise IOError('Invalid path: %s' % path)
    elif path:
        hutch_python.constants.EPICS_ARCH_FILE_PATH = path


def set_path(exp_name):
    """
    Figure out the huch name from the experiment and set the path with it.

    Parameters
    ----------
    exp_name : str
        Experiment name, e.g.: xpplv6818
    """
    if exp_name:
        hutch_python.constants.EPICS_ARCH_FILE_PATH = (
            EPICS_ARCH_FILE_PATH.format(exp_name[0:3])
        )


def print_dry_run(exp_name):
    """
    Print to stdout the data that would be stored in the epicsArch file.

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
    Return a list of items that would be written in the epicsArch file.

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
    items = get_items(exp_name)

    if items:
        for item in items:
            name = ''.join(('* ', item.name))
            data_list.append(name)
            data_list.append(item.prefix)
    return data_list


def get_items(exp_name):
    """
    Get all_items from Questionnaire.

    Parameters
    ----------
    exp_name : str
        Experiment name, e.g.: xpplv6818

    Returns
    -------
    items : list
        List of all_items from Questionnaire.
    """
    try:
        # TODO: maybe i should be using get_qs_objs here from qs_load?
        # i'd need to split it into two - i only need client.all_items
        qs_client = happi.Client(database=QSBackend(exp_name,
                                 use_kerberos=True))
    except Exception as ex:
        logger.error('Failed to load the Questionnaire, %s', ex)
        raise ex
    items = qs_client.all_items
    if not items:
        logger.warning("No devices found in PCDS Questionnaire for %s",
                       exp_name)
        return
    return items


def create_file(exp_name, path=None):
    """
    Create a file with aliases and pvs from the questionnaire.

    Parameters
    ----------
    exp_name : str
        Experiment name, e.g.: xpplv6818
    path : str, optional
        Directory where to create the epicsArch file. E.g.: /my/directory/path/
    """
    data_list = get_questionnaire_data(exp_name)
    path = path or hutch_python.constants.EPICS_ARCH_FILE_PATH
    if not os.path.exists(path):
        raise IOError('Invalid path: %s' % path)
    exp_name = str(exp_name)
    file_path = ''.join((path, 'epicsArch_', exp_name, '.txt'))

    logger.info('Creating epicsArch file for experiment: %s', exp_name)

    with open(file_path, 'w') as f:
        for data in data_list:
            try:
                f.write(f'{data}\n')
            except OSError as ex:
                logger.error('Could not write file %s, %s', file_path, ex)


def main():
    """Execute the ``epics_arch`` with command line arguments."""
    epics_arch_qs(sys.argv[1:])
