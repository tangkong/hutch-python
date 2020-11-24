from pathlib import Path

CAMVIEWER_CFG = '/reg/g/pcds/pyps/config/{}/camviewer.cfg'

CONDA_BASE = Path('/reg/g/pcds/pyps/conda/py36')

CUR_EXP_SCRIPT = '/reg/g/pcds/engineering_tools/{0}/scripts/get_curr_exp {0}'

CLASS_SEARCH_PATH = ['pcdsdevices.device_types']

EPICS_ARCH_FILE_PATH = '/cds/group/pcds/dist/pds/{}/misc/'

DIR_MODULE = Path(__file__).resolve().parent

FILE_YAML = DIR_MODULE / 'logging.yml'

HUTCH_COLORS = dict(
    amo='38;5;27',
    sxr='38;5;250',
    xpp='38;5;40',
    xcs='38;5;93',
    mfx='38;5;202',
    cxi='38;5;196',
    mec='38;5;214')

INPUT_LEVEL = 5

SUCCESS_LEVEL = 35

VALID_KEYS = ('hutch', 'db', 'load', 'experiment', 'daq_platform')
NO_LOG_EXCEPTIONS = (KeyboardInterrupt, SystemExit)
