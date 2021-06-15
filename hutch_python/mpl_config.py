# noqa
# If no environment variable set, try qt5 (best for hutch-python)
import os
os.environ.setdefault('MPLBACKEND', 'Qt5Agg')
# Force matplotlib to pick a backend
import matplotlib.pyplot
