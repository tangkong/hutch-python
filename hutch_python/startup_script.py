"""
Initialize the ELogPoster callback and subscribe it to the RunEngine

Startup script files to be run after ipython is initialized via:
``c.InteractiveTerminalApp.exec_files``

Code here will take executed after both IPython has been loaded and
the namespace has been populated with hutch objects.

These will be run as standalone python files, and should not be
imported from.
"""

import IPython
from nabs.callbacks import ELogPoster

from hutch_python.utils import safe_load

if __name__ == '__main__':
    with safe_load('ELogPoster'):
        # RE, ELog will already exist by now
        elogc = ELogPoster(elog, IPython.get_ipython())  # noqa
        RE.subscribe(elogc)  # noqa
