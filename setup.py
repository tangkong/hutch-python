import versioneer
from setuptools import setup, find_packages

setup(name='hutch-python',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      license='BSD',
      author='SLAC National Accelerator Laboratory',
      packages=find_packages(),
      include_package_data=True,
      description=('Launcher and Config Reader for '
                   'LCLS Interactive IPython Sessions'),
      entry_points={'console_scripts': [
            'hutch-python=hutch_python.cli:main',
            'epicsarch-qs=hutch_python.epics_arch:main']}
      )
