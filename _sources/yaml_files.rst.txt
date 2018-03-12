Yaml Files
==========

``hutch-python`` uses a ``conf.yml`` file for basic configuration. This is a
standard yaml file with four valid keys:
``hutch``, ``db``, ``load``, and ``experiment``.


hutch
-----

The ``hutch`` key expects a single string, the hutch name.

.. code-block:: YAML

   hutch: xpp


This key is used to:

- pick objects to load from ``happi``
- automatically select the active experiment
- create the correct ``daq`` object
- create the ``xxx.db`` module
- display the hutch banner


db
--

The ``db`` key expects a single string, the file path.

.. code-block:: YAML

   db: /reg/g/pcds/pyps/apps/hutch-python/device_config/db.json


The file path can be either relative to the ``conf.yml`` file or absolute.
In practice, you would only change this string for development purposes.

This key is used to:

- load objects from ``happi``
- set up the ``xxx_beampath`` object


load
----

The load key expects a string or a list of strings, the modules to load.

.. code-block:: YAML

   load: xpp.beamline


.. code-block:: YAML

   load:
     - xpp.beamline
     - xpp.random_stuff


Both of these formats are valid.

This key is used to include hutch-specific code.
``hutch-python`` will attempt to do a
``from module import *`` for each of these modules.


experiment
----------

The ``experiment`` key expects a dictionary with proposal and run, both
strings. It is not needed to provide an experiment key unless you would like
to load an experiment other than the active experiment; handy for debugging.

.. code-block:: YAML

   experiment:
     proposal: ls25
     run: 16


This key is used to force the questionnaire and experiment file to be from a
particular experiment.


Full File Example
-----------------

.. code-block:: YAML

   hutch: xpp

   db: /reg/g/pcds/pyps/apps/hutch-python/device_config/db.json

   load:
     - xpp.beamline
