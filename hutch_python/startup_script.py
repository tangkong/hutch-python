"""
Initialize the ELogPoster callback and subscribe it to the RunEngine

Startup script files to be run after ipython is initialized via:
``c.InteractiveTerminalApp.exec_files``

Code here will take executed after both IPython has been loaded and
the namespace has been populated with hutch objects.

These will be run as standalone python files, and should not be
imported from.
"""


def _configure_elog_poster():
    import IPython
    from nabs.callbacks import ELogPoster

    from hutch_python.utils import safe_load

    with safe_load('ELogPoster'):
        # RE, ELog will already exist by now
        elog = globals().get('elog', None)
        RE = globals().get('RE', None)
        assert elog is not None

        elogc = ELogPoster(elog, IPython.get_ipython())
        RE.subscribe(elogc)


if __name__ == '__main__':
    _configure_elog_poster()
