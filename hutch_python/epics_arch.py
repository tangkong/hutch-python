"""Module to help create the epicsArch file that will be read by the DAQ."""
import argparse
import logging
import os
import sys

from .qs_load import get_qs_client

from .constants import EPICS_ARCH_FILE_PATH

logger = logging.getLogger(__name__)


def _create_parser():
    """Argument Parser Setup. Define shell commands."""
    parser = argparse.ArgumentParser(description='Create an epicsArch file '
                                                 'from the Quesionnaire')

    parser.add_argument('experiment', help='Experiment name to'
                        ' create the epicsArch file from. E.g.: xpplv6818')

    parser.add_argument('--hutch', action="store",
                        help='Overrides hutch detection from the experiment '
                        'name. E.g.: xpp', default=None)

    parser.add_argument('--path', action="store",
                        help='Directory path where to create the epicsArch '
                        'file. E.g.: /path/to/the/directory/', default=None)

    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='Print to stdout what would be written in the '
                        'archFIle.')
    return parser


def main():
    """Entry point."""
    parser = _create_parser()
    parsed_args = parser.parse_args()
    kwargs = vars(parsed_args)
    create_arch_file(**kwargs)


def create_arch_file(experiment, hutch=None, path=None, dry_run=False):
    """
    Create an epicsArch file for the experiment.

    Parameter
    ---------
    experiment : str
        Experiment name, e.g.: `xpplv6818`
    hutch : str
        Hutch name if other than the one from the experiment, e.g.: `xcs`
    path : str
        Directory where to create the file if other than the default one which
        is `/cds/group/pcds/dist/pds/{}/misc/`
    dry_run : bool
        To indicate if only print to stdout the data that would be stored
        in the epicsArch file and not create the file.

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
    file_path = None
    if experiment and not dry_run:
        # set the path to write the epicsArch file to.
        if path:
            if path and not os.path.exists(path):
                raise IOError('Invalid path: %s' % path)
            file_path = path
        elif hutch:
            file_path = EPICS_ARCH_FILE_PATH.format(hutch.lower())
        else:
            file_path = EPICS_ARCH_FILE_PATH.format(experiment[0:3])
        create_file(exp_name=experiment, path=file_path)
    elif dry_run:
        print_dry_run(experiment)


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
        qs_client = get_qs_client(exp_name)
    except Exception as ex:
        logger.error('Failed to load the Questionnaire, %s', ex)
        raise ex
        sys.exit()
    items = qs_client.all_items
    if not items:
        logger.warning("No devices found in PCDS Questionnaire for %s",
                       exp_name)
        return
    return items


def create_file(exp_name, path):
    """
    Create a file with aliases and pvs from the questionnaire.

    Parameters
    ----------
    exp_name : str
        Experiment name, e.g.: `xpplv6818`
    path : str
        Directory where to create the epicsArch file.
    """
    data_list = get_questionnaire_data(exp_name)
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


if __name__ == '__main__':
    main()
