from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import platypus

setup(name='platypus',
  version=platypus.__version__,
  description='A Python LDP client',
  url='http://github.com/platypus-ldp/platypus',
  author='rlskoeser, barmintor, cmh2166, jrhoads',
  author_email='platypus-ldp@googlegroups.com',
  license='MIT',
  packages=['platypus'],
  zip_safe=False)
