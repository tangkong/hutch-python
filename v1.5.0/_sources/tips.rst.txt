===============
Tips and Tricks
===============


Using Partial for Scan Variants
-------------------------------
Suppose in an experiment you're always calling a function with a particular
argument, or at a hutch you want a specially-named scan for a motor that is
used every shift. You can write custom variants of any scan using a
Python built-in, ``functools.partial``

.. code-block:: python

   from bluesky.plans import scan
   from functools import partial
   from hutch.db import my_motor

   # Put arguments in early
   my_scan = partial(scan, [], my_motor)

   # Now we only need to provide start, stop, number of points
   RE(my_scan(0, 100, num=10))
