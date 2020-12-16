import logging
from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output

import pytest

logger = logging.getLogger(__name__)
tstpython = Path(__file__).parent / 'tstpython'


def test_tstpython_scripts():
    logger.debug('test_tstpython_scripts')

    good_text = check_output([tstpython, 'script.py'])
    assert b'script ran' in good_text

    try:
        bad_text = check_output([tstpython, 'bad_script.py'], stderr=STDOUT)
    except CalledProcessError as err:
        bad_text = err.output
    assert b'Traceback' in bad_text
    assert b'ZeroDivisionError' in bad_text


try:
    import colorama  # noqa
    has_colorama = True
except ImportError:
    has_colorama = False


# See bluesky.log, ophyd.log for places where colorama is initialized
# This is supposed to be safe but apparently colorama is buggy
@pytest.mark.skipif(has_colorama,
                    reason=('IPython breaks in a pseudo-tty if any package '
                            'initializes colorama, ruining this test.'))
def test_tstpython_ipython():
    logger.debug('test_tstpython_ipython')

    # This should show the banner, check if the name unique_device exists, and
    # then exit. There should be no NameError.
    ipy_text = check_output([tstpython], universal_newlines=True,
                            input='unique_device\n')
    assert 'IPython' in ipy_text
    assert 'NameError' not in ipy_text
