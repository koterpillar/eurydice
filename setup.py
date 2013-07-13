"""
Setup script
"""
from platform import python_version
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

INSTALL_REQUIRES = [
    'gevent >= 0.13.8',
    'gevent-websocket >= 0.3.6',
]

if python_version() < '2.7.0':
    INSTALL_REQUIRES += ['importlib >= 1.0.2']

DEPENDENCY_LINKS = []

if python_version() >= '3.0.0':
    INSTALL_REQUIRES += ['websocket-client-py3 >= 0.11.0']
    DEPENDENCY_LINKS += [
        'https://github.com/liris/websocket-client/archive/py3.zip' +
        '#egg=websocket-client-py3-0.11.0',
        'https://github.com/fantix/gevent/archive/master.zip' +
        '#egg=gevent-0.13.8',
    ]
else:
    INSTALL_REQUIRES += ['websocket-client >= 0.11.0']


class RunTests(TestCommand):  # pylint:disable=too-many-public-methods
    """
    Setuptools test command to run py.test
    """
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        modules = ['eurydice', 'tests']
        errno = [0]

        import pytest
        errno.append(pytest.main(modules))

        modules += ['setup.py']

        import pylint.lint
        pylint_result = pylint.lint.Run(modules, exit=False)
        errno.append(pylint_result.linter.msg_status)

        import pep8
        pep8style = pep8.StyleGuide()
        pep8style.paths = modules
        report = pep8style.check_files()
        if report.total_errors:
            errno.append(1)

        sys.exit(max(*errno))


setup(
    name="eurydice",
    version="0.1",
    packages=['eurydice'],
    install_requires=INSTALL_REQUIRES,
    tests_require=['pep8', 'pylint', 'pytest'],
    dependency_links=DEPENDENCY_LINKS,
    cmdclass={'test': RunTests},
)
