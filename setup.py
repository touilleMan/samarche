#!/usr/bin/env python3

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


class Tox(TestCommand):
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        errno = tox.cmdline(args=shlex.split(self.tox_args))
        sys.exit(errno)


DESCRIPTION = 'Samarche for testing your public api against regression !'
try:
    LONG_DESCRIPTION = open('README.md').read()
except:
    LONG_DESCRIPTION = None

VERSION = "0.0.1"

CLASSIFIERS = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    "Programming Language :: Python :: 3",
]

setup(name='samarche',
      version=VERSION,
      author='Emmanuel Leblond',
      author_email='emmanuel.leblond@{nospam}gmail.com',
      url='https://github.com/touilleMan/samarche',
      download_url='https://github.com/touilleMan/samarche/tarball/master',
      license='MIT',
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      platforms=['any'],
      classifiers=CLASSIFIERS,
      py_modules=['samarche'],
      tests_require=['tox'],
      cmdclass={'test': Tox})
