"""
Setup script
"""
from platform import python_version
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

INSTALL_REQUIRES = []

if python_version() < '2.7.0':
    INSTALL_REQUIRES += ['importlib >= 1.0.2']

class PyTest(TestCommand): # pylint:disable=too-many-public-methods
    """
    Setuptools test command to run py.test
    """
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="pypl",
    version="0.1",
    packages=['pypl'],
    install_requires=INSTALL_REQUIRES,
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)
