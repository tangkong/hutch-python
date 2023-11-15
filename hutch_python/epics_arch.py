"""Module to help create the epicsArch file that will be read by the DAQ."""
import argparse
import logging
import os
import sys
import warnings

from collections import OrderedDict
from .constants import EPICS_ARCH_FILE_PATH
from .qs_load import get_qs_client
from itertools import chain
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
                        'archFile.')

    # parser.add_argument('--update', action='store_true', default=False,
    #                     help='Check the current archFile for existing relevant qsdata. If constains,'
    #                     ' then update with the new information.'
    #                     ' If not, overwrite the existing file with the new data.')
    return parser


def main():
    """Entry point."""
    print("\nepicsarch-qs test script, git")
    parser = _create_parser()
    parsed_args = parser.parse_args()
    kwargs = vars(parsed_args)
    create_arch_file(**kwargs)


def create_arch_file(experiment, hutch=None, path=None, dry_run=False, update=False):
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
    update : bool
        To look into the qsdata and update the epicsArch file instead of overwriting it.

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
                raise OSError('Invalid path: %s' % path)
            file_path = path
        elif hutch:
            file_path = EPICS_ARCH_FILE_PATH.format(hutch.lower())
        else:
            file_path = EPICS_ARCH_FILE_PATH.format(experiment[0:3])
        create_file(exp_name=experiment, path=file_path)
    elif dry_run:
        print_dry_run(experiment)
    # elif update:
    #     print("\n IN UPDATE CASE")
    #     update_questionaire_data(experiment)

def check_for_duplicates(exp_name):
    # print("\nChecking for updates")
    # print("\nExp Name: " + exp_name + " Hutch: " + exp_name[0:3])

    """Get live questionaire data"""
    qsData = get_questionnaire_data(exp_name)

    # print("\nNew Data")
    # sorted(qsData)
    # print(qsData)

    """Get local questionaire data"""
    # if after doesnt exist, opt to create one

    afData = read_archfile(EPICS_ARCH_FILE_PATH.format(exp_name[0:3]) + 'epicsArch_' + exp_name + '.txt')
    afData = [r.replace("\n", "") for r in afData]
    # print(afData)

    """
    Now check for duplicate PVs in the qs data, the code already throws a warning for duplicate aliases.
    If found the local epicsArch file PVs and the questionaire PVs have different aliases than take the alias of the questionaire.
    """

    # Dictionary approach
    
    # convert lists to dictionaries to sort. removing any spaces in the aliases and sorting dictionaries


    # Questionnaire
    qsDict = dict(zip(qsData[::2], qsData[1::2]))
    qsDict = {k.replace(" ", ""):v for k,v in qsDict.items()}
    sorted_qsDict = dict(sorted(qsDict.items()))
    

    # ArchFile
    afDict = dict(zip(afData[::2], afData[1::2]))
    afDict = {k.replace(" ", ""):v for k,v in afDict.items()}
    sorted_afDict = dict(sorted(afDict.items()))
    


    
    # Check the questionaire for duplicate PVs

    # Making reverse multidict to help identify duplicate values in QSD
    rev_keyDict = {}
    for key, value in sorted_qsDict.items():
        rev_keyDict.setdefault(value, list()).append(key) 
    pvDuplicate = [key for key, values in rev_keyDict.items() if len(values) > 1]
    # print("Rev Dict:\n")
    # print(rev_keyDict)
    # Looking for duplicates of PVs in the questionaire
    # also print out the alias for PV, change removing to warning operater to remove dup then rerun
    for dup in pvDuplicate:
        # warnings.warn("!Duplicate PV in questionnaire!:" + str(dup))
        print("!Duplicate PV in questionnaire!:" + str(dup))
        for value in rev_keyDict[dup][1:]:
            print("Found PV duplicate(s) from questionnaire: " + value + ", " + sorted_qsDict[value])
            # del sorted_qsDict[value]
        raise Exception("Please remove duplicates and re-run script!")

    # print("\nLocal Dictionary")
    # print(sorted_afDict)
    # print("\nLive Sorted Dictionary")
    # print(sorted_qsDict)

    
    # Checking for matching aliases in the questionaire and archfile
    # if the alias has a match then update the PV
    for k in sorted_qsDict.keys():
        if k in sorted_afDict:
            # print("\n(PV Match) Updating Entry: " + k + ", " + sorted_qsDict[k])
            print("!Alias Match in questionnaire and archfile! Updating PV: " + k + ", " + sorted_qsDict[k])
            sorted_afDict[k] = sorted_qsDict[k]
    # print("\nUpdated Local Directory:\n")
    # print( sorted_afDict)

    # Checking for matching PVs in QSD and EAF
    # if the PV matches update the alias by removing the old key and making a new one
    for (k,val) in sorted_qsDict.items():
        # print(sorted_afDict[k])
        # print("qsDict: "+qsDict[index])
        # if val in sorted_afDict.values():
        # this looks up the key in the af Dictionary by finding the value
        foundKey = get_key(val, sorted_afDict)
        if foundKey:
            del sorted_afDict[foundKey]
        sorted_afDict[k] = val

        # print("\n(PV Match) Updating Entry: " + k + ", " + sorted_qsDict[k])
        print("!PV Match in questionnaire and archfile! Updating Alias: " + k + ", " + val)
    # print("\n Final sorted afDict:\n")
    sorted_afDict = dict(sorted(afDict.items()))
    # print(sorted_afDict)


    updated_arch_list = [x for item in sorted_afDict.items() for x in item]

    # print("Updated ArchFile: \n")
    # for i in updated_arch_list:
    #     print(i)
    return updated_arch_list

def read_archfile(exp_path):
    # print("\nREADING EXISTING ARCHFILE")
    # print("\nArchFile Path: \n"+exp_path)

    """First try with readlines()"""
    with open(exp_path, "r") as experiment:
        lines = experiment.readlines()
        # sorted(lines)
        # print(lines)
    return lines  

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
    """
    Updating experiment file.
    """
    updated_archFile = check_for_duplicates(exp_name)

    data = get_questionnaire_data(exp_name)
    for item in data:
        print(item)
def get_key(val, my_dict):
    for k, v in my_dict.items():
        if val == v:
            return k
    strError = ""
    return strError

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
        raise OSError('Invalid path: %s' % path)
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
