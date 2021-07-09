# If no environment variable set, try qt5 (best for hutch-python)
import os
os.environ.setdefault('MPLBACKEND', 'Qt5Agg')
# Matplotlib will choose an appropriate backend based on the environment
# variable settings and its ability to communicate with an X server.
# Our preference, as above, is to use the Qt5 backend when available.
import matplotlib.pyplot  # noqa: F401 E402
