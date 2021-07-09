Debug
=====

There are numerous debug features built in to ``hutch-python``.

Live Session Logging
--------------------

The first place to go when something has already gone wrong is to the log
files. These are stored in a ``logs`` directory in the same location as the
``conf.yml`` file, and sorted by date and session start time.

These contain every log message from the session in the order they were called.
Each module can choose when to make calls to ``logger.debug`` to generate
log messages, but we also log every single input line, output line, and
exception that was raised in the interactive session. Note that the input and
output lines are not available to the logger until the entire command has
executed, so the log messages immediately preceding an input log are those
that were created by calling that statement.

The logging configuration is specified by the ``logging.yaml`` file and is
set up by the :py:mod:`log_setup` module. If not in debug mode, only log levels
``INFO`` and above will make it to the terminal. The files are configured to
rotate and roll over into a second file once they get too large.

PCDS-wide Logging
-----------------

A special Python logger for PCDS-wide logging is pre-configured within
``hutch-python``.  This special logger is named ``'pcds-logging'``, and hooks
in with our managed logstash, ElasticSearch and Grafana stack.  

To explore the data, access Grafana `here
<https://pswww.slac.stanford.edu/ctl/grafana/explore>`_.

To record information, first get the logger itself:

.. code-block:: python
   
    import logging
    pcds_logger = logging.getLogger('pcds-logging')


Log messages above the configured level (by default ``logging.DEBUG``) will be
transmitted to the centralized log server to be recorded and indexed.

One example use case is when an important event that would be useful to see
trended over time:

.. code-block:: python
   
    pcds_logger.info('I dropped the sample')


Or for exception statistics, perhaps. The following will include a full stack
trace along with module and line information automatically:


    try:
        1/0
    except ZeroDivisionError:
        pcds_logger.exception('This specific thing went wrong')


It is not necessary to include information about the host that is running
Python, module versions, or thread/process names as these are automatically
included.


Debug Mode
----------

You can start in debug mode by passing the ``--debug`` option to
``hutch-python``. Debug mode changes the logging configuration to print
log messages of level ``DEBUG`` and above to the screen.
Within every session, we have a few hidden objects for managing the
state of debug mode.

- `_debug_mode <hutch_python.log_setup.debug_mode>`:
        Used to enable, disable, or check the state of debug mode.
- `_debug_context <hutch_python.log_setup.debug_context>`:
        Context manager for enabling debug mode for a block of code.
- `_debug_wrapper <hutch_python.log_setup.debug_wrapper>`:
        Wrapper for enabling debug mode for the execution of a single
        function.
- `_debug_console_level <hutch_python.log_setup.set_console_level>`:
        Utility function for setting the console's logging level to an
        arbitrary value.


.. code-block:: python

   _debug_mode(True)     # Turn on debug mode
   _debug_mode(False)    # Turn off debug mode
   print(_debug_mode())  # Check debug mode

   # Turn on debug mode for the duration of a code block
   with _debug_context():
       buggy_function(arg)

   # Turn on debug mode for one function call
   _debug_wrapper(buggy_function, arg)


Automated Test Logging
----------------------

If you're running the automated test suite, each test run is stored in a
module-level ``logs`` folder. This can be useful for diagnosing why the tests
are failing.
